from dotenv import load_dotenv
from openai import OpenAI
import os
import pydash as _

# ENV
load_dotenv()

# TODO: GOOGLE (Connecting to Drive for paper persistence)

# DeepSeek
openai_client = OpenAI(api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")
