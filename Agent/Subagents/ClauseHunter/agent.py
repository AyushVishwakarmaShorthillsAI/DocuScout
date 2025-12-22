from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .Subagents.Gliner.agent import root_agent as gliner_agent
from .Subagents.LexNLP.agent import root_agent as lexnlp_agent
# from .Subagents.RAG.agent import root_agent as rag_agent  # RAG disabled for now
from .tools import fetch_raw_extraction_results, save_curated_playbook, export_playbook_to_disk

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

# 1. Parallel Execution Group (The Harvester)
# This agent runs the specialized tools concurrently.
clause_harvester = ParallelAgent(
    name="ClauseDataHarvester",
    sub_agents=[gliner_agent, lexnlp_agent],
    description="Harvests raw legal data (clauses, entities, risks) from documents by running gliner_agent and lexnlp_agent concurrently."
)

# 2. Aggregator Agent (The Builder)
# This agent collects the raw data and builds the final playbook.
clause_finder_agent = LlmAgent(
    name="ClauseFinderAgent",
    model=lite_llm_model,
    tools=[fetch_raw_extraction_results, save_curated_playbook, export_playbook_to_disk],
    description="Fetches raw data from the session, filters/deduplicates it, and saves the final Playbook.",
    instruction="""You are the ClauseFinderAgent. Your goal is to build a high-quality 'Dynamic Playbook' from raw extraction data.

**Your Tools:**

1. `fetch_raw_extraction_results()` 
   - Retrieves combined extraction results from GLiNER and LexNLP subagents
   - Returns legal entities organized by filename
   - No parameters required

2. `save_curated_playbook(curated_playbook_json)` 
   - Saves your curated playbook JSON to session state
   - Parameter: curated_playbook_json (string) - The playbook JSON as a string

3. `export_playbook_to_disk()` 
   - Writes the saved playbook to `dynamic_playbook.json` file
   - No parameters required

**Workflow:**

Step 1: Call `fetch_raw_extraction_results()` to get extraction data from the Harvester.

Step 2: Analyze the data and create a curated playbook JSON with this EXACT structure:

```json
{
    "playbook": [
        {
            "filename": "LeaseOffice.pdf",
            "legal_entities": ["California Consumer Privacy Act", "GDPR", "Section 7"]
        },
        {
            "filename": "SampleContract.pdf",
            "legal_entities": ["Minimum Wages Act", "Article 1", "Clause 3.2"]
        }
    ]
}
```

When creating the playbook:
- Each entry in "playbook" array represents ONE document file
- Use the EXACT filename from Step 1 results (e.g., "LeaseOffice.pdf", not "document1.pdf")
- Combine entities from GLiNER and LexNLP for each file
- Merge duplicate entities within each file's legal_entities array
- Only include entities explicitly found in source documents
- Filter out hallucinations or entities not present in the source
- "legal_entities" must be an array of strings
- Do NOT create nested structures or add extra fields

Step 3: Call `save_curated_playbook(curated_playbook_json)` with your JSON as a string.

Step 4: Call `export_playbook_to_disk()` to write the playbook file.

**CRITICAL:**
- ONLY use these 3 tools: fetch_raw_extraction_results, save_curated_playbook, export_playbook_to_disk
- DO NOT call other agents or invent tool names
- DO NOT try to call clause_finder or any other non-existent tools
"""

)

# 3. Sequential Orchestrator (The Pipeline)
# This agent ensures the Harvester runs FIRST, and THEN the ClauseFinder runs.
playbook_pipeline = SequentialAgent(
    name="PlaybookPipeline",
    sub_agents=[clause_harvester, clause_finder_agent],
    description="Agent that execute two subagents in sequence: Firstly call clause_harvester, then call clause_finder_agent."
)

# 4. Root Orchestrator (The Interface)
# This is the main entry point that the System Orchestrator sees.
# It simply delegates to the pipeline.
root_agent = LlmAgent(
    name="ClauseHunter",
    model=lite_llm_model,
    tools=[],
    sub_agents=[playbook_pipeline],
    description="You are the ClauseHunter. You oversee the creation of the Legal Playbook.",
    instruction="""Directly run the `PlaybookPipeline` agent. 
If the pipeline completes successfully, inform the user 'Dynamic Playbook generated successfully."""
)

