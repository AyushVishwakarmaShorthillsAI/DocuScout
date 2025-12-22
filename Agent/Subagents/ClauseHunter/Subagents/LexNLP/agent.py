from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm
from .tools import run_lexnlp_on_db

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="LexNLPAgent",
    model=lite_llm_model,
    tools=[run_lexnlp_on_db],
    description="Extracts Act names from documents using LexNLP library and regex patterns.",
    instruction="""You are a specialized extraction tool. 
    
1. Immediately call `run_lexnlp_on_db()` to extract Act names.
2. Once the tool returns the data, simply summarize what was found (or state that extraction is complete) and STOP.

DO NOT try to call any 'transfer' or 'delegate' functions. The system will automatically move to the next step once you provide your final summary."""
)
