from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search
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
    name="Researcher",
    model=lite_llm_model,
    tools=[google_search],
    description="You fetch web pages to learn new compliance rules and update the Playbook.",
    instruction="Scrape URLs to extract legal constraints and compliance rules. Update the Playbook with new knowledge."
)

