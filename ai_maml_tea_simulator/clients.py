from dotenv import load_dotenv
from openai import OpenAI
import os
import pydash as _

# ENV
load_dotenv()

# TODO: GOOGLE (Connecting to Drive for paper persistence)

# OPENAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
