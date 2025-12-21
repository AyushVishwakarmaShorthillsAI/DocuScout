import os
import json
import asyncio
import time
import logging
from typing import List
from google.adk.tools.tool_context import ToolContext
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# Helper function for a single blocking search (run in thread)
def _execute_single_search(client, law_name: str, jurisdiction: str, whitelist_domains: List[str]) -> str:
    search_start = time.time()
    try:
        # Construct specific query for recent updates AND summary
        query = f"what is {law_name} official summary and latest amendments {jurisdiction} 2024 2025"
        
        logger.info(f"[Researcher Tools] 🔍 Starting Tavily search for: {law_name}")
        logger.info(f"[Researcher Tools] 📝 Query: {query}")
        logger.info(f"[Researcher Tools] 🌐 Whitelist domains: {whitelist_domains}")
        
        # Execute Search
        search_api_start = time.time()
        response = client.search(
            query=query,
            search_depth="advanced",
            include_domains=whitelist_domains,
            max_results=5
        )
        search_api_elapsed = time.time() - search_api_start
        
        logger.info(f"[Researcher Tools] ⏱️  Tavily API call completed in {search_api_elapsed:.2f}s for: {law_name}")
        
        # Format results
        results_text = f"--- Search Results for '{law_name}' (2024-2025 Updates) ---\n"
        if not response.get("results"):
            logger.warning(f"[Researcher Tools] ⚠️  No results found for: {law_name}")
            results_text += f"No recent official updates found on allowed domains.\n"
        else:
            num_results = len(response["results"])
            logger.info(f"[Researcher Tools] ✅ Found {num_results} results for: {law_name}")
            for idx, result in enumerate(response["results"]):
                title = result.get("title", "No Title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content snippet")
                content_length = len(content) if content else 0
                logger.debug(f"[Researcher Tools]   Result {idx+1}: {title} ({content_length} chars)")
                results_text += f"SOURCE: {title} ({url})\nSNIPPET: {content}\n\n"
        
        total_elapsed = time.time() - search_start
        logger.info(f"[Researcher Tools] ✅ Search completed for '{law_name}' in {total_elapsed:.2f}s")
        return results_text

    except Exception as e:
        elapsed = time.time() - search_start
        logger.error(f"[Researcher Tools] ❌ Error searching for '{law_name}' after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[Researcher Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error searching for {law_name}: {str(e)}\n"

async def batch_search_legal_updates(tool_context: ToolContext, law_names: List[str], jurisdiction: str = "India") -> str:
    """
    Simultaneously searches for official legal amendments and summaries for multiple laws.
    
    Args:
        tool_context: The tool execution context.
        law_names: A list of law/act names (e.g., ["Minimum Wages Act", "Income Tax Act"]).
        jurisdiction: The jurisdiction (default "India").
        
    Returns:
        A combined string containing search results for ALL requested laws.
    """
    function_start = time.time()
    logger.info("=" * 100)
    logger.info(f"[Researcher Tools] 🚀 batch_search_legal_updates() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[Researcher Tools] 📥 Parameters:")
    logger.info(f"[Researcher Tools]   - law_names: {law_names} ({len(law_names)} laws)")
    logger.info(f"[Researcher Tools]   - jurisdiction: {jurisdiction}")
    
    # 1. Secured "Walled Garden" Whitelist
    whitelist_domains = [
        "indiacode.nic.in",      # Official Central Acts
        "legislative.gov.in",    # Legislative Department
        "egazette.nic.in",       # Official Gazette (Notifications)
        "rbi.org.in",            # Reserve Bank of India
        "sebi.gov.in",           # SEBI
        "mca.gov.in",            # Ministry of Corporate Affairs
        "indiankanoon.org",      # Case Law / Act Text Search
        "clc.gov.in"             # Chief Labour Commissioner
    ]
    logger.info(f"[Researcher Tools] 🌐 Whitelist domains: {whitelist_domains}")
    
    # Check for Tavily API Key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("[Researcher Tools] ❌ TAVILY_API_KEY not found in environment variables")
        return "Error: TAVILY_API_KEY not found in environment variables."

    try:
        logger.info("[Researcher Tools] 🔑 Tavily API key found, initializing client...")
        # Initialize Client
        client = TavilyClient(api_key=api_key)
        logger.info("[Researcher Tools] ✅ Tavily client initialized")
        
        # Create Loop for Parallel Execution
        # We use asyncio.to_thread because the Tavily Python client is blocking (synchronous)
        loop = asyncio.get_running_loop()
        tasks = []
        
        logger.info(f"[Researcher Tools] 📋 Creating {len(law_names)} parallel search tasks...")
        for idx, law in enumerate(law_names):
            logger.info(f"[Researcher Tools]   Task {idx+1}/{len(law_names)}: {law}")
            tasks.append(
                loop.run_in_executor(None, _execute_single_search, client, law, jurisdiction, whitelist_domains)
            )
        
        # Run all searches concurrently
        logger.info(f"[Researcher Tools] 🚀 Starting parallel execution of {len(tasks)} searches...")
        parallel_start = time.time()
        results = await asyncio.gather(*tasks)
        parallel_elapsed = time.time() - parallel_start
        
        logger.info(f"[Researcher Tools] ✅ All {len(results)} searches completed in {parallel_elapsed:.2f}s")
        
        # Combine all results into one massive string
        combined_result = "\n\n".join(results)
        result_length = len(combined_result)
        total_elapsed = time.time() - function_start
        
        logger.info(f"[Researcher Tools] 📊 Results summary:")
        logger.info(f"[Researcher Tools]   - Total result length: {result_length} characters")
        logger.info(f"[Researcher Tools]   - Parallel execution time: {parallel_elapsed:.2f}s")
        logger.info(f"[Researcher Tools]   - Total function time: {total_elapsed:.2f}s")
        logger.info("=" * 100)
        
        return combined_result

    except Exception as e:
        elapsed = time.time() - function_start
        logger.error(f"[Researcher Tools] ❌ Error in batch_search_legal_updates after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[Researcher Tools] 📋 Traceback:\n{traceback.format_exc()}")
        logger.info("=" * 100)
        return f"Error performing batch legal search: {str(e)}"

async def read_playbook_entities(tool_context: ToolContext) -> str:
    """
    Reads the 'dynamic_playbook.json' from session state or disk and extracts unique legal entities.
    Returns: A formatted string list of Laws, Acts, and Regulations to research.
    """
    function_start = time.time()
    logger.info(f"[Researcher Tools] 📖 read_playbook_entities() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try session state first
    logger.info("[Researcher Tools] 🔍 Checking session state for 'clausehunter:playbook'...")
    playbook_data = tool_context.state.get("clausehunter:playbook")
    
    if playbook_data:
        logger.info("[Researcher Tools] ✅ Found playbook in session state")
    else:
        logger.info("[Researcher Tools] ⚠️  Playbook not in session state, trying disk...")
        # Fallback to disk if missing (e.g. fresh restart)
        if not playbook_data:
            try:
                logger.info("[Researcher Tools] 📂 Attempting to read dynamic_playbook.json from disk...")
                with open("dynamic_playbook.json", "r") as f:
                    playbook_data = json.load(f)
                logger.info(f"[Researcher Tools] ✅ Successfully read playbook from disk ({len(str(playbook_data))} chars)")
            except FileNotFoundError:
                logger.error("[Researcher Tools] ❌ dynamic_playbook.json not found on disk")
                return "Error: No playbook found. Please run ClauseHunter first."
            except Exception as e:
                logger.error(f"[Researcher Tools] ❌ Error reading playbook file: {type(e).__name__}: {str(e)}")
                return f"Error reading playbook: {str(e)}"

    if not playbook_data:
        logger.error("[Researcher Tools] ❌ Playbook is empty")
        return "Error: Playbook is empty."

    # Extract unique entities
    logger.info("[Researcher Tools] 🔍 Extracting unique legal entities from playbook...")
    entities = set()
    playbook_keys = list(playbook_data.keys()) if isinstance(playbook_data, dict) else []
    logger.info(f"[Researcher Tools] 📋 Playbook structure: {len(playbook_keys)} top-level keys")
    
    for filename, content in playbook_data.items():
        if isinstance(content, dict):
            for category in ["laws", "acts", "regulations"]:
                if category in content:
                    items = content[category]
                    if isinstance(items, list):
                        logger.debug(f"[Researcher Tools]   Processing {len(items)} items in {category} for {filename}")
                        for item in items:
                            if isinstance(item, dict) and "text" in item:
                                entities.add(item["text"])
    
    unique_list = sorted(list(entities))
    tool_context.state["researcher:targets"] = unique_list
    
    elapsed = time.time() - function_start
    logger.info(f"[Researcher Tools] ✅ Extracted {len(unique_list)} unique legal entities in {elapsed:.2f}s")
    logger.info(f"[Researcher Tools] 📋 Entities: {unique_list[:10]}{'...' if len(unique_list) > 10 else ''}")
    
    return f"Found {len(unique_list)} unique legal entities in playbook: {', '.join(unique_list)}"

async def save_compliance_updates(tool_context: ToolContext, compliance_json: str) -> str:
    """
    Saves the researched compliance updates to 'compliance_updates.json'.
    Args:
        compliance_json: The JSON string containing the findings.
    """
    function_start = time.time()
    logger.info(f"[Researcher Tools] 💾 save_compliance_updates() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[Researcher Tools] 📥 Input JSON length: {len(compliance_json)} characters")
    
    try:
        # Validate JSON
        logger.info("[Researcher Tools] 🔍 Validating JSON format...")
        parsed = json.loads(compliance_json)
        logger.info(f"[Researcher Tools] ✅ JSON valid, parsed structure: {type(parsed)}")
        
        if isinstance(parsed, dict):
            updates = parsed.get("updates", [])
            logger.info(f"[Researcher Tools] 📊 Found {len(updates)} compliance updates in JSON")
        
        # Save to file
        filename = "compliance_updates.json"
        logger.info(f"[Researcher Tools] 💾 Writing to {filename}...")
        write_start = time.time()
        with open(filename, "w") as f:
            json.dump(parsed, f, indent=4)
        write_elapsed = time.time() - write_start
        
        file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
        elapsed = time.time() - function_start
        
        logger.info(f"[Researcher Tools] ✅ Successfully saved {filename}")
        logger.info(f"[Researcher Tools] 📊 File size: {file_size} bytes")
        logger.info(f"[Researcher Tools] ⏱️  Write time: {write_elapsed:.2f}s, Total: {elapsed:.2f}s")
        
        return f"Success: Compliance updates saved to {filename}"
        
    except json.JSONDecodeError as e:
        logger.error(f"[Researcher Tools] ❌ Invalid JSON format: {str(e)}")
        logger.error(f"[Researcher Tools] 📋 JSON snippet (first 500 chars): {compliance_json[:500]}")
        return "Error: Invalid JSON format provided."
    except Exception as e:
        elapsed = time.time() - function_start
        logger.error(f"[Researcher Tools] ❌ Error saving file after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[Researcher Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error saving file: {str(e)}"
