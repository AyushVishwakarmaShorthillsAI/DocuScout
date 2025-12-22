from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .tools import run_opennyai_on_db

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model="hackathon-gemini-2.5-flash",
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

root_agent = LlmAgent(
    name="OpenNyAIAgent",
    model=lite_llm_model,
    tools=[run_opennyai_on_db],
    description="Specialized agent using the OpenNyAI Spacy model tuned for Indian and Commonwealth legal documents.",
    instruction="Use the `run_opennyai_on_db` tool for extracting Indian and Commonwealth legal entities. The tool accepts an optional `db_path` parameter (defaults to 'DB'). It employs a specific Spacy NER model trained on Indian legal datasets to accurately identify and label 'Statute' and 'Provision' entities within the text."
)
