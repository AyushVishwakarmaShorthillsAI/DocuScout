from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
from .tools import run_rag_extraction_on_db

import os
import litellm

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="RAGAgent",
    model=lite_llm_model,
    tools=[run_rag_extraction_on_db],
    description="Part of ClauseHunter's Harvester. Specialized agent using Semantic Search (RAG) to find complex clauses and answer conceptual queries.",
    instruction="""You are part of the ClauseHunter agent's Harvester component.
    
    Your ONLY task: Call `run_rag_extraction_on_db(query_focus)` to perform semantic searches for complex legal concepts.
    
    The tool requires a `query_focus` parameter (string) specifying the topic to extract (e.g., 'Indemnity Clauses', 'Termination'). 
    It uses Google File Search to analyze document context and synthesize summaries of:
    - Articles
    - Sections
    - Specific Acts (IPC, CrPC)
    
    **CRITICAL:**
    - ONLY use the `run_rag_extraction_on_db` tool
    - DO NOT call other tools or agents (like clause_finder, ClauseFinder, etc.)
    - DO NOT invent tool names
    - You are ONE component of a larger ClauseHunter workflow
    """
)
