from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

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
    name="Greeter",
    model=lite_llm_model,
    description="You greet users and explain what DocuScout is.",
    instruction="Greet users warmly and explain that DocuScout is an intelligent risk radar for contracts and documents. It helps users understand legal documents by analyzing them for potential risks, highlighting dangerous clauses, and answering questions about documents. Do not transfer to other agents - provide the response yourself."
)

