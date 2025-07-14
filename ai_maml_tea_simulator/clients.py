from dotenv import load_dotenv
from openai import OpenAI
import os
import pydash as _

# ENV
load_dotenv()

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()

# TODO: GOOGLE (Connecting to Drive for paper persistence)

# OPENAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
deepseek_client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def get_llm_client():
    if LLM_PROVIDER == "deepseek":
        return deepseek_client
    return openai_client

def get_llm_model(model=None):
    if LLM_PROVIDER == "deepseek":
        return model or "deepseek-chat"
    return model or "gpt-4-turbo-preview"
