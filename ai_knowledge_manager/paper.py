from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import List, Optional
import pypdf
import urllib.parse
import yaml
from .prompts import prompt_detail_extraction, prompt_figure_description
from .scrapers import scrape_sync


class Section(BaseModel):
    is_additional_section: bool
    content: str

class PaperSource(BaseModel):
    link: str
    linktype: Optional[str] = None

class Paper(BaseModel):
    id: Optional[str] = Field(None, alias='doi')
    describes_process: Optional[str] = None
    source: Optional[PaperSource] = None # Condensing sources of papers into a single json entry
    html: Optional[str] = None
    title: Optional[str] = None
    sections: List[Section] = [] #TODO: Rename to accessible_text
    references: List[str] = [] # Might discard but keeping for now
    doi: Optional[str] = None
    text_abstract: Optional[str] = None
    text_novelty: Optional[str] = None               # write how the processes or approach as described in this paper differ from similar approaches. Keep this shorter than 5 sentences.
    text_irr: Optional[str] = None                   # write a summary of the paper's reflection on internal rate of return (IRR). Keep this shorter than 3 sentences.
    text_price_sensitivity: Optional[str] = None     # write a summary of the paper's reflection on price sensitivity. Keep this shorter than 3 sentences.
    tags_doe: Optional[List[str]] = []
    tags_feedstocks: Optional[List[str]] = []
    tags_target_product: Optional[List[str]] = []

    class Config:
        populate_by_name = True

    class Text(BaseModel):
        text: str
        name: str
        embeddings: Optional[List[float]] = None

    def init(self, paper_source: PaperSource):
        self.source = paper_source

    def load_html(self, url: str):
        """Loading HTML from URL for processing"""
        print("[Paper.load_html]")
        # V1: requests (doesn't work if delay loading)
        # html = requests.get(url)
        # self.html = html.text
        # V2: pyppeteer (works with delay loading)
        self.html = scrape_sync(url)

    def fulltext(self) -> str:
        """Return title and sections content as single string"""
        if not self.title:
            title = ""
        else:
            title = self.title
        sections_to_join = filter(lambda section: not section.is_additional_section, self.sections)
        return title + "\n\n" + "\n\n".join([section.content for section in sections_to_join])

    def get_paper_data(self):
        print("[Paper.get_paper_data]")
        return self.dict()

    def parse_text(self, text: str):
        """Hacky way to grab text and get the basic structure for now"""
        print("[Paper.parse_text]")
        self.title = prompt_detail_extraction(text[0:500], "What is the title of this paper?")
        self.doi = prompt_detail_extraction(text, "What is the DOI for this paper? (Ex: https://doi.org/10.1038/srep20361, https://doi.org/10.4161/bioe.19874)")
        self.id = self.doi
        # HACK: just want text into this structure so i can use it downstream
        self.sections = [{
            "content": text,
            "is_additional_section": False,
        }]

    def parse(self):
        """Determine which HTML parser to use based on URL"""
        print("[Paper.load]")
        #removed old cache check here.
        # URLS
        if self.source.linktype == "url":
            # --- load
            self.load_html(self.url)
            # --- parse URLs
            if "nature.com" in self.url:
                self.parse_html_nature()
            if "nih.gov" in self.url:
                self.parse_html_nih()
            return
        # TEXT
        if ".txt" in self.source.link:
            with open(self.source.link, 'r') as file:
                text = file.read()
                self.parse_text(text)
            return
        if ".pdf" in self.source.link:
            text = self.read_pdf_basic(self.source.link)
            self.parse_pdf(text)
            return
        print(f"Nothing loaded because source={self.source.dict()}")

    def parse_pdf(self, text: str):
        """Hacky way to grab text and get the basic structure for now"""
        print("[Paper.parse_pdf]")
        if not self.title:
            self.title = prompt_detail_extraction(text[0:500], "What is the title of this paper?")
        if not self.doi:
            self.doi = prompt_detail_extraction(text, "What is this paper's DOI as a valid URL? (Ex: https://doi.org/10.1038/srep20361, https://doi.org/10.4161/bioe.19874)")
        if not self.id:
            self.id = self.doi

        # HACK: just want text into this structure so i can use it downstream
        self.sections = [{
            "content": text,
            "is_additional_section": False,
        }]

    def read_pdf_basic(self, filename):
        # Initialize an empty string to hold all text
        output_text = ""
        # Open the PDF file
        with open(filename, "rb") as pdfFileObj:
            # Create a PDF reader object
            pdfReader = pypdf.PdfReader(pdfFileObj)
            # Iterate through each page and append text to output_text
            for page in pdfReader.pages:
                page_text = page.extract_text() or ""  # Ensure we get a string even if None is returned
                output_text += page_text
        # Now output_text contains all text from the PDF
        return output_text

    def parse_html_nature(self):
        """HTML Parser: Nature Journal"""
        soup = BeautifulSoup(self.html, "html.parser")
        soup_article = soup.article #unused?
        soup_article_header = soup.select("article div.c-article-header") #unused?
        soup_article_body = soup.select("article div.c-article-body") #unused?
        soup_article_body_sections = soup.select("article section")
        soup_bibliography_items = soup.select("li.c-bibliographic-information__list-item")
        soup_h1 = soup.h1
        # --- compile content
        self.title = soup_h1.text
        self.doi = None
        self.sections = []
        self.references = []
        # --- compile DOI (will be used as ID)
        for item in soup_bibliography_items:
            if 'DOI' in item.get_text():
                doi_value_span = item.find('span', class_='c-bibliographic-information__value')
                if doi_value_span:
                    self.doi = doi_value_span.get_text().strip()
                    self.id = self.doi
                    break
        # --- compile html elements after each h2
        is_additional_section = False # note if a sections is past main content
        for section in soup_article_body_sections:
            section_h2 = section.find("h2")
            # skip if no header
            if section_h2 == None: continue
            # stop compiling sections when we hit references, this focuses on content might be bad str
            if section_h2.text == "Reference" or section_h2.text.lower() == "Additional Information":
                is_additional_section = True
                # TODO: parse links to cited papers if we need to pull additional info
            # content prep
            section_content = section.select(".c-article-section__content")
            y = yaml.dump(section_content[0].text)
            section_content_yaml = y.replace("\\\n  \\ ", "").replace("\n  ", "").strip()
            # interpret figures and splice that into the section content
            section_figures = section.select("figure")
            for figure in section_figures:
                figure_title_text = figure.select_one("figcaption").text
                figure_description_select = figure.select(".c-article-section__figure-description")
                figure_description_select_text = figure_description_select[0].text if len(figure_description_select) > 0 else None
                # ... if an image TODO: not sure if we'll need to handle multiple images, for now assuming there's 1 per figure
                figure_image_select = figure.select("img")
                figure_image_select_url = figure_image_select[0].attrs["src"] if len(figure_image_select) > 0 else None
                if figure_image_select_url != None:
                    figure_image_structured_data = prompt_figure_description(f"{figure_title_text}, {figure_description_select_text}", "https:" + figure_image_select_url)
                    section_content_yaml = section_content_yaml.replace(figure_title_text, figure_title_text + " " + figure_image_structured_data)
                # ... TODO: if a table
            # append to the yaml_sections
            self.sections.append({
                "html": str(section), # saving raw info if we want to reprocess/parse later
                "title": section_h2.text,
                "content": section_content_yaml,
                "is_additional_section": is_additional_section # non-critical
            })

    def parse_html_nih(self):
        """HTML Parser: NIH"""
        soup = BeautifulSoup(self.html, "html.parser")
        soup_article = soup.select_one("#mc") #unused?
        soup_article_header = soup.select_one("h1") #unused?
        soup_article_body = soup.select_one(".jig-ncbiinpagenav") #unused?
        soup_bibliography_items = soup.select(".ref-cit-blk") #unused?
        soup_article_body_sections = soup.select("div.tsec.sec")
        soup_h1 = soup.h1
        # --- compile content
        self.title = soup_h1.text
        self.doi = None
        self.sections = []
        self.references = []
        # --- compile DOI (will be used as ID)
        soup_doi = soup.select_one("span.doi a")
        if soup_doi:
            self.doi = urllib.parse.unquote("https:" + soup_doi.attrs["href"])
            self.id = self.doi
        # --- compile html elements after each h2
        is_additional_section = False # note if a sections is past main content
        for section in soup_article_body_sections:
            section_h2 = section.find("h2")
            # skip if no header
            if section_h2 == None: continue
            # stop compiling sections when we hit references, this focuses on content might be bad str
            if section_h2.text == "References" or section_h2.text.lower() == "Additional Information":
                is_additional_section = True
                # TODO: parse links to cited papers if we need to pull additional info
            # content prep
            section_content = section.findChildren()
            # ...since figures are weaving in-between paragraphs, we'll loop over both figures + text
            section_content_yaml = ""
            for section in section_content:
                # ... if h2 or goto div, skip
                if section.name == "h2" or "goto" in section.get("class", []):
                    continue
                # ... if text
                if section.name == "p" and "p" in section.get("class", []):
                    y = yaml.dump(section.text)
                    section_content_yaml += y.replace("\\\n  \\ ", "").replace("\n  ", "").strip()
                    section_content_yaml += "\n\n"
                # ... if figure
                if section.name == "div" and "fig" in section.get("class", []):
                    figure_caption_text = section.select_one(".caption")
                    figure_image_select = section.select_one("img")
                    figure_image_select_url = figure_image_select.attrs["src"]
                    if figure_image_select_url != None:
                        figure_image_structured_data = prompt_figure_description(figure_caption_text, "https://www.ncbi.nlm.nih.gov" + figure_image_select_url)
                        section_content_yaml += figure_image_structured_data
                        section_content_yaml += "\n\n"
                # ... if table (TODO: insert as structured data rather than free text)
                if section.name == "div" and "table-wrap" in section.get("class", []):
                    y = yaml.dump(section.text)
                    section_content_yaml += y.replace("\\\n  \\ ", "").replace("\n  ", "").strip()
                    section_content_yaml += "\n\n"
            # append to the yaml_sections
            self.sections.append({
                "html": str(section), # saving raw info if we want to reprocess/parse later
                "title": section_h2.text,
                "content": section_content_yaml,
                "is_additional_section": is_additional_section # non-critical
            })
