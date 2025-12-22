from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .tools import ingest_documents


load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)
root_agent = LlmAgent(
    name="FileReader",
    model=lite_llm_model,
    tools=[ingest_documents],
    description="You read and extract text from document files.",
    instruction="Extract text from uploaded documents and prepare it for analysis. Use the ingest_documents tool to upload files to Google File Search."
)

