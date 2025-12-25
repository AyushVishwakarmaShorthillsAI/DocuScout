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
    instruction="""You are a specialized legal entity extractor.
    
1. Immediately call `run_gliner_on_db()` to extract Statutes, Acts, Provisions, Regulations, and Amendments.
    
2. After the tool returns the results, provide a brief final summary of the extraction status and then STOP. 

IMPORTANT: Do NOT attempt to call any 'transfer' or 'delegate' functions. The parent orchestrator will handle the workflow automatically once you provide your final text response."""
)
