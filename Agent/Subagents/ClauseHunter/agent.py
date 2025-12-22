from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

from .Subagents.Gliner.agent import root_agent as gliner_agent
from .Subagents.LexNLP.agent import root_agent as lexnlp_agent
from .Subagents.RAG.agent import root_agent as rag_agent
from .tools import fetch_raw_extraction_results, save_curated_playbook, export_playbook_to_disk

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model="hackathon-gemini-2.5-flash",
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

# 1. Parallel Execution Group (The Harvester)
# This agent runs the specialized tools concurrently.
clause_harvester = ParallelAgent(
    name="ClauseDataHarvester",
    sub_agents=[gliner_agent, lexnlp_agent],
    description="Harvests raw legal data (clauses, entities, risks) from documents by running Gliner, LexNLP, and RAG concurrently."
)

# 2. Aggregator Agent (The Builder)
# This agent collects the raw data and builds the final playbook.
clause_finder_agent = LlmAgent(
    name="ClauseFinder",
    model=lite_llm_model,
    tools=[fetch_raw_extraction_results, save_curated_playbook, export_playbook_to_disk],
    description="Fetches raw data from the session, filters/deduplicates it, and saves the final Playbook.",
    instruction="""
    You are the 'ClauseFinder'. Your goal is to build a high-quality 'Dynamic Playbook' from raw extraction data.
    
    Workflow:
    1. Call `fetch_raw_extraction_results()` to get the combined outputs from the Harvester.
    2. Analyze the data and create a curated playbook following the EXACT structure below:
       - Merge duplicate clauses.
       - Only include entities that are explicitly found in the source documents.
       - Filter out any entities that appear to be hallucinations or not present in the source.
    3. Call `save_curated_playbook(curated_playbook_json)` to save the result.
    4. Call `export_playbook_to_disk()` to write the file.
    
    REQUIRED JSON STRUCTURE:
    Your playbook MUST follow this exact format:
    
    {
        "playbook": [
            {
                "filename": "document1.pdf",
                "legal_entities": ["California Consumer Privacy Act", "GDPR", "Section 7 (Warranties)"]
            },
            {
                "filename": "document2.pdf",
                "legal_entities": ["Minimum Wages Act", "Article 1", "Clause 3.2"]
            }
        ]
    }
    
    IMPORTANT:
    - Each entry in the "playbook" array represents ONE document file
    - "filename" must be the exact PDF filename from the extraction results
    - "legal_entities" is an array of ALL unique legal terms, clauses, acts, and provisions found in that file
    - Combine entities from GLiNER, LexNLP, and RAG for each file
    - Remove duplicates within each file's legal_entities array
    - Do NOT create nested structures or add extra fields
    """
)

# 3. Sequential Orchestrator (The Pipeline)
# This agent ensures the Harvester runs FIRST, and THEN the ClauseFinder runs.
playbook_pipeline = SequentialAgent(
    name="PlaybookPipeline",
    sub_agents=[clause_harvester, clause_finder_agent],
    description="Executes the Playbook generation pipeline: first harvest data (in parallel), then compile the playbook."
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

If the pipeline completes successfully, inform the user 'Dynamic Playbook generated successfully.' 

If you encounter any errors (such as 'No message in response' or empty LLM responses), the PlaybookPipeline should automatically use fallback mechanisms to create a playbook from raw extraction data. In such cases, still inform the user that the playbook was generated, even if using fallback methods."""
)

