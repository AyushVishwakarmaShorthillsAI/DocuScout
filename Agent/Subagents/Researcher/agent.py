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

from .tools import batch_search_legal_updates, read_playbook_entities, save_compliance_updates

root_agent = LlmAgent(
    name="Researcher",
    model=lite_llm_model,
    tools=[batch_search_legal_updates, read_playbook_entities, save_compliance_updates],
    description="You verify legal terms from the Playbook and retrieve official 2024-2025 amendments.",
    instruction="""
    You are the 'Legal Researcher Agent'. Your goal is to keep the Playbook up-to-date with the latest Indian laws.

    Workflow:
    1. **Fetch**: Call `read_playbook_entities()` to get the raw list of items found in the documents.
    2. **Identify**: Analyze the returned list.
       - Use your knowledge to identify which items are valid **Laws, Acts, or Regulations** (e.g., "Minimum Wages Act", "GDPR").
       - Ignore noise or irrelevant text.
       - Create a LIST of these valid law names.
    3. **Batch Research**:
       - Call `batch_search_legal_updates(law_names=[...])` ONCE with the full list of laws.
       - Do NOT call the tool multiple times. Send all laws in one request for parallel processing.
    4. **Synthesize**:
       - Analyze the combined search results.
       - **DESCRIBE**: Summarize what each law governs.
       - **UPDATE**: Detail 2024-2025 changes for each.
       - CITE SOURCES.
    5. **Report**:
       - Compile a final JSON object: `{"updates": [{"law": "...", "description": "...", "status": "...", "latest_change": "...", "source": "..."}]}`
       - Call `save_compliance_updates(json_string)` to save it to disk.
       - Inform the user "Compliance check complete. Report saved."
    """
)

