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

from .tools import batch_search_legal_updates, read_playbook_entities, save_compliance_updates

root_agent = LlmAgent(
    name="Researcher",
    model=lite_llm_model,
    tools=[batch_search_legal_updates, read_playbook_entities, save_compliance_updates],
    description="You verify legal terms from the Playbook and retrieve official 2024-2025 amendments.",
    instruction="""
    You are the 'Legal Researcher Agent'. Your goal is to research legal entities from the playbook and provide compliance updates.

    Workflow:
    1. **Read Playbook**: Call `read_playbook_entities()` to get legal entities organized by filename.
       - The tool will return entities grouped by their source files
       - It will also show all unique legal entities found across all files
    
    2. **Identify Valid Laws**: Analyze the returned entities.
       - Identify which items are valid **Laws, Acts, or Regulations** (e.g., "Minimum Wages Act", "GDPR", "California Consumer Privacy Act")
       - Ignore generic terms like "Section 7", "Article 1" unless they reference specific acts
       - Create a LIST of valid law names to research
    
    3. **Batch Research**: Call `batch_search_legal_updates(law_names=[...])` ONCE with the full list.
       - Do NOT call the tool multiple times
       - Send all laws in one request for parallel processing
    
    4. **Synthesize Results**: Analyze the search results and create a comprehensive report.
       - For each law, provide: law_name, description, status, latest_change, and source
       - Use the search results to determine if there were 2024-2025 amendments
    
    5. **Generate Final Report**: Create a JSON array with this EXACT structure:
    
    [
        {
            "filename": "LeaseOffice.pdf",
            "laws": [
                {
                    "law_name": "Minimum Wages Act",
                    "description": "Detailed description of what this law governs",
                    "status": "Update identified",
                    "latest_change": "Description of 2024-2025 amendments",
                    "source": "https://indiacode.nic.in/..."
                },
                {
                    "law_name": "ESI Act",
                    "description": "...",
                    "status": "No recent amendments",
                    "latest_change": "No recent changes",
                    "source": "..."
                }
            ]
        },
        {
            "filename": "Contract document.pdf",
            "laws": [
                {
                    "law_name": "California Consumer Privacy Act",
                    "description": "...",
                    "status": "...",
                    "latest_change": "...",
                    "source": "..."
                },
                {
                    "law_name": "GDPR",
                    "description": "...",
                    "status": "...",
                    "latest_change": "...",
                    "source": "..."
                }
            ]
        }
    ]
    
    IMPORTANT:
    - Each entry represents ONE document file
    - "laws" is an ARRAY of law objects, NOT a comma-separated string
    - Each law object must have: law_name, description, status, latest_change, source
    - Group laws by their source filename (use the filenames from step 1)
    - If a file has multiple laws, they should all be in the "laws" array for that file
    - **CRITICAL**: ONLY use the tools provided to you (read_playbook_entities, batch_search_legal_updates, save_compliance_updates)
    - DO NOT call tools from other agents or invent tool names
    - DO NOT try to call RiskAuditor or any other agent's tools
    
    6. **Save**: Call `save_compliance_updates(json_string)` with your JSON array.
    
    7. **Inform**: Tell the user "Compliance research complete. Report saved to compliance_updates.json"
    """
)

