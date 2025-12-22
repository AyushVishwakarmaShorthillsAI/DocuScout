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
         - For EACH file that contains the law, call `fetch_law_context_from_document(law_name, filename)` to read the ACTUAL clause from the contract text.
         - Store the findings grouped by filename.
         
    3. **Gap Analysis (Thinking Step)**:
       - For each file, analyze all laws found in that file:
         - **Constraint Check**: Does the contract clause contradict the new rule? (e.g., Contract says "₹300 wage", Law update says "₹500 wage"). -> VIOLATION.
         - **Silence Check**: Is the law mentioned but the specific mandated requirement missing? -> MISSING.
         - **Compliance Check**: Is the contract aligned? -> SAFE.

    4. **Reporting (CRITICAL: FILE-WISE ORGANIZATION)**:
       - Generate a Markdown report with the following EXACT structure:
         
         ```markdown
         # Legal Compliance Audit Report: 2024-2025 Legal Updates
         
         ## Executive Summary
         [Brief overview of all findings across all files]
         
         ## Detailed Findings by File
         
         ### File: Contract document.pdf
         
         #### Minimum Wages Act, 1948
         - **2024-2025 Amendment**: [summary from compliance updates]
         - **Contract Clause**: [exact text from the document, include page number if available]
         - **Gap Analysis**: 🟡 **Risk/Warning** - [explanation of the issue]
         - **Recommendation**: [specific action for this file]
         
         #### Information Technology Act, 2000
         - **2024-2025 Amendment**: [summary]
         - **Contract Clause**: Not found in document
         - **Gap Analysis**: 🔴 **Violation** - [explanation]
         - **Recommendation**: [specific action]
         
         ### File: Another document.pdf
         [Repeat structure for each file]
         ```
       
       - **CRITICAL REQUIREMENTS**:
         - Organize ALL findings by filename FIRST, then by law within each file
         - Each file gets its own "### File: [filename]" section
         - Within each file section, list ALL laws/issues found in that specific file
         - If a law appears in multiple files, it should appear in EACH file's section separately
         - Use emojis: 🔴 for Violation, 🟡 for Risk/Warning, 🟢 for Compliant
         - Include page numbers when available from `fetch_law_context_from_document`
         - If a file has no issues, you can skip it or add "No compliance issues identified"
       
       - Call `save_audit_report(report_md)` to save it.
    """
)

