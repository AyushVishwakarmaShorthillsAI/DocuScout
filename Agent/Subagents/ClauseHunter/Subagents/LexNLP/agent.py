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
    description="Extracts structured legal data using LexNLP library and regex patterns.",
    instruction="""Immediately call `run_lexnlp_on_db()` to extract structured legal data from documents.
    
    The tool uses LexNLP library and regex to extract: Act names, Monetary amounts, Dates, Case citations.
    
    **Your Task:**
    1. Call `run_lexnlp_on_db()` (accepts optional db_path, defaults to 'DB')
    2. Return the results
    3. Done
    
    **CRITICAL:**
    - Do NOT call transfer_to_agent or any coordination tools
    - Do NOT try to communicate with other agents
    - ONLY use run_lexnlp_on_db
    - Just execute your tool and return
    """
)
