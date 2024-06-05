from dotenv import load_dotenv
from openai import OpenAI
import os
import pydash as _

# ENV
load_dotenv()

# OPENAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
