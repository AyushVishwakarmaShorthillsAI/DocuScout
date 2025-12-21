from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm
from .tools import run_lexnlp_on_db

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model="gemini-2.5-flash",
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="LexNLPAgent",
    model=lite_llm_model,
    tools=[run_lexnlp_on_db],
    description="Specialized agent using the LexNLP library to extract structured data based on regex patterns.",
    instruction="Use the `run_lexnlp_on_db` tool to extract precise structured data values. The tool accepts an optional `db_path` parameter (defaults to 'DB'). It utilizes the LexNLP library and regular expressions to reliably extract and format data types including Act names, monetary amounts (with currency), dates, and case citations."
)
