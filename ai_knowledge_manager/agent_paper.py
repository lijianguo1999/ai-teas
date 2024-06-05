
import pydash as _
import time
from .prompts import prompt_assess_paper_type, prompt_paper_meta, prompt_tags_from_paper
from .paper import Paper, PaperSource


# AGENT: PAPER/HTML PARSER
class PaperAgent(): 
    def __init__(self, persistence=None):
        self.paper = None
        # setup focuses on persistence, paper loading/parsing is separate method
        self.persistence = persistence
        self.persistence.load_paper_graph() # just ensuring we have most recent data/graph
        
    def assess_paper_type(self):
        start_time = time.time()
        dict_results = prompt_assess_paper_type(self.paper.fulltext())
        end_time = time.time()
        print(f"[Paper.assess_paper_type]: Took {end_time - start_time} seconds")
        if "response" not in dict_results:
            print(f"Strange error, no response in dict_results: {dict_results}")
            dict_results["response"] = next(iter(dict_results.values()))
        return dict_results["response"]

    def load_paper(self, link: str):
        self.paper = self.persistence.retrieve_paper_from_store(link)
        # if no paper found, let's parse one and save it to using persistence methods
        if self.paper is None:
            # init paper & run load func to parse data
            self.paper = Paper(source=PaperSource(link=link))
            self.paper.parse()
            # persist
            self.persistence.save_paper(self.paper)
        
    def save_paper(self):
        self.persistence.save_paper(self.paper)
        return self.paper

    def process_paper(self, force: bool = False):
        print(f"[PaperAgent.process_paper] processing paper (force={force})...")
        # SHORT CIRCUIT: if paper has already been parsed aka there's a 'describes_process' prop
        if self.paper.describes_process != None and force != True:
            print(f"[PaperAgent.process_paper] paper has already been processed, skipping")
            return self.paper
        # Assesss if we're talking about review vs. single process since content focus will differ greatly
        self.paper.describes_process = self.assess_paper_type() 
        # IF describing a novel/single process
        if self.paper.describes_process == "single_process":
            # summaries about paper, novelty, tecnoeconomics described
            paper_meta = prompt_paper_meta(self.paper.fulltext())
            # update paper props
            self.paper.text_abstract = paper_meta.get("abstract")
            self.paper.text_novelty = paper_meta.get("novelty")
            if paper_meta.get("has_irr") == True:
                self.paper.text_irr = paper_meta.get("irr")
            if paper_meta.get("has_price_sensitivity") == True:
                self.paper.text_price_sensitivity = paper_meta.get("price_sensitivity")
            # tags for filtering/search/analysis
            paper_tags = prompt_tags_from_paper(self.paper.fulltext())
            self.paper.tags_doe = paper_tags.get("tags_doe")
            self.paper.tags_feedstocks = paper_tags.get("tags_feedstocks")
            self.paper.tags_target_product = paper_tags.get("tags_target_product")
        # IF review paper (or clearly not single process), skip
        else:
            print(f"[PaperAgent.process_paper] Paper is a review, not summarizing it.")
        return self.paper 
