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
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)

# 1. Parallel Execution Group (The Harvester)
# This agent runs the specialized tools concurrently.
clause_harvester = ParallelAgent(
    name="ClauseDataHarvester",
    sub_agents=[gliner_agent, lexnlp_agent, rag_agent],
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
    
    CRITICAL INSTRUCTION: You MUST follow these steps successfully IN ORDER. Do not skip steps.
    
    1. **FETCH DATA**: Call `fetch_raw_extraction_results()` to get the input data.
    
    2. **PROCESS**: Analyze the data to create a curated playbook JSON.
       - Merge duplicates.
       - Select high confidence entities.
       - Format as JSON.
    
    3. **SAVE (MANDATORY)**: Call `save_curated_playbook(curated_playbook_json)` to save your JSON to the session.
       - **WARNING**: You MUST do this BEFORE step 4. If you skip this, Step 4 will fail.
    
    4. **EXPORT**: Call `export_playbook_to_disk()` to write the file.
    
    If you encounter errors, stop and report them.
    """
)

# 3. Sequential Orchestrator (The Pipeline)
# This agent ensures the Harvester runs FIRST, and THEN the ClauseFinder runs.
playbook_pipeline = SequentialAgent(
    name="PlaybookPipeline",
    sub_agents=[clause_harvester, clause_finder_agent],
    description="Runs firstly the clause_harvester, then the clause_finder_agent in order."
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
    
    If the pipeline completes successfully, inform the user 'Dynamic Playbook generated successfully.'.
    If there are errors, report them details."""
)

