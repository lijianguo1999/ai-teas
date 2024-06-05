import datetime
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gspread_dataframe import get_as_dataframe, set_with_dataframe
import json
import os
import os.path
import pickle
from .paper import Paper, PaperSource


class Persistence:
    def retrieve_paper_from_store(self, identifier):
        """Retrieve a paper from the storage by its identifier.
            Returns None if the paper is not found.
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def save_paper(self, paper):
        """Save a paper object to the storage."""
        raise NotImplementedError("Subclass must implement abstract method")


# ####################################
# LOCAL: JSON

class JSONPersistence(Persistence):
    def __init__(self, cache_path: str):
        self._paper_graph_path = cache_path
        self._paper_graph = None
        self.load_paper_graph()

    def load_paper_graph(self):
        """Load paper graph cache for checking if we've parsed it already"""
        print("[JSONPersistence.load_paper_graph]")
        # Create Graph Cache if None Exists
        if os.path.exists(self._paper_graph_path) == False:
            print("[JSONPersistence.load_paper_graph] No paper graph file found, creating one")
            with open(self._paper_graph_path, 'w') as file:
                json.dump({}, file)
        # Load Graph Cache
        with open(self._paper_graph_path, 'r') as file:
            self._paper_graph = json.load(file)

    def retrieve_paper_from_store(self, identifier):
        # Loop over all the items in the file see if there's 
        for key, value in self._paper_graph.items():
            # print(f"Checking {value.get('file_path')} against {identifier}")
            if value.get("source").get("link") == identifier:
                print(f"[JSONPersistence.retrieve_paper_from_store] Paper loaded from cache: {value.get('source').get('link')}") 
                # Create the pydantic class from dictionary
                return Paper(**value)
        return None

    def save_paper(self, paper):
        """Save paper data to a JSON file in the cache directory"""
        print("[JSONPersistence.save]")
        # Append this paper to graph (key on DOI)
        if not paper.doi:
            raise ValueError("DOI is missing for the paper")
        # Load a dict of the paper data
        self._paper_graph[paper.id] = paper.get_paper_data()
        # IO: Update JSON graph file
        with open(self._paper_graph_path, 'w') as file:
            json.dump(self._paper_graph, file, indent=4)


# ####################################
# REMOTE: GOOGLE DRIVE
# TODO: WORK IN PROGRESS implemention the GDrivePersistence class to feature parity with JSONPersistence

# login to gDocs
# This should work providigin the user is running from the root directory and the file exists
PATH_CREDENTIALS = 'google-app-credentials.json'
# Raw Papers root directory:
ROOT_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_ROOT_FOLDER_ID")
#For making the review template
GSHEET_TEMPLATE_LINK = "https://docs.google.com/spreadsheets/d/{}/edit"
GDRIVE_FILE_VIEW_TEMPLATE = "https://drive.google.com/file/d/{}/view"
# TEMPLATE_ID = os.environ.get("GOOGLE_DRIVE_TEMPLATE_ID")
#For accesing the main coordination doc
COORDINATION_DOC_ID = os.environ.get("GOOGLE_DRIVE_COORDINATION_DOC_ID")
COORDINATION_DOC_SUMMARIES = 'PaperSummaries'
COORDINATION_DOC_ALL = 'TotalLibrary'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
# REVIEWER_TEMPLATE_CELLS_TO_CHECK = os.environ.get("GOOGLE_DRIVE_REVIEWER_TEMPLATE_CELLS_TO_CHECK")

class GDrivePersistence(Persistence):
    def __init__(self):
        # Initialize Google Drive connection here
        # Connect to the Google Sheets and Drive APIs
        self.creds = self.get_creds()
        self.service_drive = build('drive', 'v3', credentials=self.creds)
        self.service_sheets = build('sheets', 'v4', credentials=self.creds)
        #Load the coordination doc
        client = gspread.authorize(self.creds)
        self.spreadsheet_master = client.open_by_key(COORDINATION_DOC_ID)
        self.processed_worksheet = self.spreadsheet_master.worksheet(COORDINATION_DOC_SUMMARIES)
        self.total_papers_sheet = self.spreadsheet_master.worksheet(COORDINATION_DOC_ALL)
        self.library_df = get_as_dataframe(self.processed_worksheet, evaluate_formulas=True,)
        # Assuming the second row is your desired header and you want to skip the first row
        # Reset the header
        new_header = self.library_df.iloc[0]  # Take the second row for the header
        self.library_df = self.library_df[1:]  # Take the data less the header row
        self.library_df.columns = new_header  # Set the header row as the df header
        self.library_df.reset_index(drop=True, inplace=True)
        self.library_df = self.library_df.set_index('id')
        #set_with_dataframe(self.processed_worksheet, self.library_df)
        set_with_dataframe(self.processed_worksheet, self.library_df, row=2, col=1, include_index=True, include_column_header=True)
        self.total_library_df = get_as_dataframe(self.total_papers_sheet, evaluate_formulas=True)
        self.total_library_df = self.total_library_df.set_index('id')

    def get_creds(self):
        """
        Retrieves the user's credentials for accessing the Homeworld API.
        If the user's credentials are stored in a 'token.pickle' file, this function
        will attempt to load them from that file. If the credentials are not found
        or are invalid, the user will be prompted to authenticate via the Homeworld
        API and the new credentials will be saved to the 'token.pickle' file.
        Returns:
            Credentials: The user's credentials for accessing the Homeworld API.
        """
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    PATH_CREDENTIALS, SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def retrieve_paper_from_store(self, paper_id):
        """
        Search for a paper in the GDrive Store. if it exists, return it, if not, return None
        """
        # Check if the paper is in the library
        # cell = self.total_papers_sheet.find(f"{paper.id}")
        if paper_id in self.total_library_df.index:
            # If the ID exists, return the row as a Paper object
            paper_from_store = self.total_library_df.loc[paper_id].to_dict()
            paper_from_store['sections'] = [] # 
            paper_from_store['source'] = PaperSource(link=paper_from_store['file_path'], linktype="pdf")
            for key, value in paper_from_store.items():
                try:
                    paper_from_store[key] = json.loads(value)  # Convert from a JSON string
                except:
                    # print(f"Could not convert {key} to JSON, value: {value}")
                    pass
            return Paper(**paper_from_store )
        else:
            return None

    def save_paper_text(self, paper:Paper):
        """
        Save a paper to the GDrive store
        """  
        url_text_file = None
        url_pdf_file = None
        # Assume paper.fulltext() gives you the text content
        paper_text = paper.fulltext()
        # Get the current date in YYYYMMDD format
        current_date = datetime.datetime.now().strftime('%Y%m%d')
        # Modified temporary file path with the current date
        # get just the filename from the full path 
        local_filename = os.path.basename(paper.source.link)
        temp_file_path = f"{local_filename}_extracted_{current_date}.txt"
        # Save text to a temporary file
        with open(temp_file_path, 'w', encoding='utf-8', errors='replace') as temp_file:
            temp_file.write(paper_text)
        # Create file metadata
        file_metadata = {
            'name': temp_file_path,
            'parents': [ROOT_FOLDER_ID]
        }
        # Upload the file
        media = MediaFileUpload(temp_file_path, mimetype='text/plain')
        text_file = self.service_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        url_text_file = GDRIVE_FILE_VIEW_TEMPLATE.format(text_file.get('id'))
        os.remove(temp_file_path)  # Delete the temporary file
        if paper.source.linktype == "pdf":
            pdf_file_path = paper.source.link
            # Create file metadata for the PDF
            pdf_file_metadata = {
                'name': os.path.basename(pdf_file_path),
                'parents': [ROOT_FOLDER_ID]
            }
            # Upload the PDF file
            media_pdf = MediaFileUpload(pdf_file_path, mimetype='application/pdf')
            pdf_file = self.service_drive.files().create(body=pdf_file_metadata, media_body=media_pdf, fields='id').execute()
            # Print the PDF file ID
            url_pdf_file = GDRIVE_FILE_VIEW_TEMPLATE.format(pdf_file.get('id'))
        # Optionally, delete the temporary file
        return url_text_file, url_pdf_file

    def save_paper(self, paper:Paper):
        """
        Save a paper to the GDrive store
        """  
        print('[gDrivePersistence.save_paper]')
        paper_data = paper.get_paper_data()
        paper_data['sections'] = [] #Temporary hack 
        # The data needs to be modified to fit the dataframe
        # Loop over paper_data items and flatten sequences or complex structures to JSON strings
        for key, value in paper_data.items():
            if isinstance(value, (list, dict)):  # Check if the value is a list or dictionary
                paper_data[key] = json.dumps(value)  # Convert to a JSON string
        #A paper that has been processed and saved to the library will already have uploaded links
        if not paper.extracted_text: 
            url_text_file, url_pdf_file = self.save_paper_text(paper)
            # Add the URL to the text file and the PDF file to the paper data
            paper_data['extracted_text'] = url_text_file
            paper_data['file_path'] = url_pdf_file
        # Save the paper to the processed worksheet, 
        # 'id' is the key, so the dictionary comprehension line is just to avoid 
        # double-saving the id value
        # Note: By indexing on id, we can update the row if it exists, or add a new row if it doesn't
        self.total_library_df.loc[paper_data['id']] = \
            {k: v for k, v in paper_data.items() if k != 'id'}
        print(f"Total size of total_library_df: {self.total_library_df.shape}")
        set_with_dataframe(self.total_papers_sheet, self.total_library_df,include_index=True)

