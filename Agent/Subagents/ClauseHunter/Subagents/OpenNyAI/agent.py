from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .tools import run_opennyai_on_db

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="OpenNyAIAgent",
    model=lite_llm_model,
    tools=[run_opennyai_on_db],
    description="Part of ClauseHunter's Harvester. Specialized agent using the OpenNyAI Spacy model tuned for Indian and Commonwealth legal documents.",
    instruction="""You are part of the ClauseHunter agent's Harvester component.
    
    Your ONLY task: Call `run_opennyai_on_db()` to extract Indian/Commonwealth legal entities.
    
    The tool accepts an optional `db_path` parameter (defaults to 'DB'). It uses Spacy NER trained on Indian legal datasets to identify:
    - Statutes
    - Provisions
    
    **CRITICAL:**
    - ONLY use the `run_opennyai_on_db` tool
    - DO NOT call other tools or agents (like clause_finder, ClauseFinder, etc.)
    - DO NOT invent tool names
    - You are ONE component of a larger ClauseHunter workflow
    """
)
