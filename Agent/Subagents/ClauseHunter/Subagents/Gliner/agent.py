from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .tools import run_gliner_on_db

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="GlinerAgent",
    model=lite_llm_model,
    tools=[run_gliner_on_db],
    description="Extracts legal entities using GLiNER zero-shot NER model.",
    instruction="""Immediately call `run_gliner_on_db()` to extract legal entities from documents.
    
    The tool uses zero-shot NER to identify: Statutes, Acts, Provisions, Regulations, Amendments.
    
    **Your Task:**
    1. Call `run_gliner_on_db()` (accepts optional db_path, defaults to 'DB')
    2. Return the results
    3. Done
    
    **CRITICAL:**
    - Do NOT call transfer_to_agent or any coordination tools
    - Do NOT try to communicate with other agents
    - ONLY use run_gliner_on_db
    - Just execute your tool and return
    """
)
