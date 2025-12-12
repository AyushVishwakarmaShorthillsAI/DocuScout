from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

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
    name="RiskAuditor",
    model=lite_llm_model,
    tools=[],
    description="You analyze documents for deviations from Playbook safety standards and flag risks.",
    instruction="Check document text against Playbook rules. Flag violations and assign risk levels (High, Medium, Low)."
)

