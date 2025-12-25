from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv
import os
import litellm
from .tools import query_docs

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="Consultor",
    model=lite_llm_model,
    tools=[query_docs],
    description="You are an expert consultant who answers questions based on the provided documents.",
    instruction="You are an expert consultant. Your job is to answer user questions based on the documents that have been ingested into the system. Use the 'query_docs' tool to find relevant information and generate answers."
)
