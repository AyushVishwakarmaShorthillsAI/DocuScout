from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .tools import run_gliner_on_db

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model="gemini-2.5-flash",
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="GlinerAgent",
    model=lite_llm_model,
    tools=[run_gliner_on_db],
    description="Specialized agent using the GLiNER model (Zero-shot NER) to extract a wide range of legal entities.",
    instruction="Use the `run_gliner_on_db` tool to extract broad legal entities from the documents. The tool accepts an optional `db_path` parameter (defaults to 'DB') which points to the folder containing the PDF files. It uses a zero-shot NER model to identify labels such as 'statute', 'act', 'provision', 'regulation', and 'amendment'."
)
