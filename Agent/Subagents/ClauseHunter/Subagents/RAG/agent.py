from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
from .tools import run_rag_extraction_on_db

import os
import litellm

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model="gemini-2.5-flash",
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="RAGAgent",
    model=lite_llm_model,
    tools=[run_rag_extraction_on_db],
    description="Specialized agent using Semantic Search (RAG) to find complex clauses and answer conceptual queries.",
    instruction="Use the `run_rag_extraction_on_db` tool to perform semantic searches for complex legal concepts. The tool requires a `query_focus` parameter (string) which specifies the topic to extract (e.g., 'Indemnity Clauses', 'Termination'). It leverages Google File Search to analyze document context and synthesize summaries of key terms like Articles, Sections, and specific Acts (IPC, CrPC) while avoiding verbatim recitation."
)
