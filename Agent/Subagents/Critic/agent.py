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

from .tools import fetch_audit_context, fetch_law_context_from_document, save_audit_report

root_agent = LlmAgent(
    name="Critic",
    model=lite_llm_model,
    tools=[fetch_audit_context, fetch_law_context_from_document, save_audit_report],
    description="You cross-reference the Contract Playbook against Legal Updates to find compliance risks.",
    instruction="""
    You are the 'Legal Critic'. Your job is to perform a Gap Analysis between the Contract and the 2024-2025 Legal Updates.

    Workflow:
    1. **Initialize**: Call `fetch_audit_context()` to load the 'Ground Truth' (Compliance Updates) and the 'Subject' (Contract Files).
    
    2. **Verification Loop**:
       - Iterate through the laws in the Compliance Updates.
       - IF a law has a status of "Update identified" OR "No recent amendments" (but is crucial):
         - Identify which file(s) in the Playbook contain this law.
         - Call `fetch_law_context_from_document(law_name, filename)` to read the ACTUAL clause from the contract text.
         
    3. **Gap Analysis (Thinking Step)**:
       - **Constraint Check**: Does the contract clause (from step 2) contradict the new rule? (e.g., Contract says "₹300 wage", Law update says "₹500 wage"). -> VIOLATION.
       - **Silence Check**: Is the law mentioned but the specific mandated requirement missing? -> MISSING.
       - **Compliance Check**: Is the contract aligned? -> SAFE.

    4. **Reporting**:
       - Generate a Markdown report including:
         - **Executive Summary**
         - **Detailed Findings** (Use emojis: 🔴 for Violation, 🟡 for Risk/Warning, 🟢 for Compliant).
         - Cite the specific 2024-2025 Amendment source (from the Context) and the Contract Clause (from the Document Fetch).
       - Call `save_audit_report(report_md)` to save it.
    """
)

