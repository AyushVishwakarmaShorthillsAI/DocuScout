import os
import json
import asyncio
from typing import List
from google.adk.tools.tool_context import ToolContext
from tavily import TavilyClient

# Helper function for a single blocking search (run in thread)
def _execute_single_search(client, law_name: str, jurisdiction: str, whitelist_domains: List[str]) -> str:
    try:
        # Construct specific query for recent updates AND summary
        query = f"what is {law_name} official summary and latest amendments {jurisdiction} 2024 2025"
        
        # Execute Search
        response = client.search(
            query=query,
            search_depth="advanced",
            include_domains=whitelist_domains,
            max_results=5
        )
        
        # Format results
        results_text = f"--- Search Results for '{law_name}' (2024-2025 Updates) ---\n"
        if not response.get("results"):
            results_text += f"No recent official updates found on allowed domains.\n"
        else:
            for result in response["results"]:
                title = result.get("title", "No Title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content snippet")
                results_text += f"SOURCE: {title} ({url})\nSNIPPET: {content}\n\n"
        
        return results_text

    except Exception as e:
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
    
    # Check for Tavily API Key
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not found in environment variables."

    try:
        # Initialize Client
        client = TavilyClient(api_key=api_key)
        
        # Create Loop for Parallel Execution
        # We use asyncio.to_thread because the Tavily Python client is blocking (synchronous)
        loop = asyncio.get_running_loop()
        tasks = []
        
        for law in law_names:
            tasks.append(
                loop.run_in_executor(None, _execute_single_search, client, law, jurisdiction, whitelist_domains)
            )
        
        # Run all searches concurrently
        results = await asyncio.gather(*tasks)
        
        # Combine all results into one massive string
        return "\n\n".join(results)

    except Exception as e:
        return f"Error performing batch legal search: {str(e)}"

async def read_playbook_entities(tool_context: ToolContext) -> str:
    """
    Reads the 'dynamic_playbook.json' from session state or disk and extracts unique legal entities.
    Returns: A human-readable string summary of legal entities organized by file.
    """
    
    # Try session state first
    playbook_data = tool_context.state.get("clausehunter:playbook")
    
    # Fallback to disk if missing (e.g. fresh restart)
    if not playbook_data:
        try:
            with open("dynamic_playbook.json", "r") as f:
                playbook_data = json.load(f)
        except FileNotFoundError:
            return "Error: No playbook found. Please run ClauseHunter first."
        except Exception as e:
            return f"Error reading playbook file: {str(e)}"

    if not playbook_data:
        return "Error: Playbook is empty."

    # Handle new structure: {"playbook": [{"filename": "...", "legal_entities": [...]}]}
    entities_by_file = []
    all_unique_entities = set()
    
    if isinstance(playbook_data, dict) and "playbook" in playbook_data:
        # New structure
        playbook_array = playbook_data.get("playbook", [])
        for entry in playbook_array:
            if isinstance(entry, dict):
                filename = entry.get("filename", "Unknown")
                legal_entities = entry.get("legal_entities", [])
                if legal_entities:
                    entities_by_file.append({
                        "filename": filename,
                        "entities": legal_entities
                    })
                    all_unique_entities.update(legal_entities)
    else:
        # Old structure fallback (for compatibility)
        for filename, content in playbook_data.items():
            file_entities = []
            if isinstance(content, dict):
                for category in ["laws", "acts", "regulations", "legal_entities"]:
                    if category in content:
                        items = content[category]
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "text" in item:
                                    file_entities.append(item["text"])
                                elif isinstance(item, str):
                                    file_entities.append(item)
            if file_entities:
                entities_by_file.append({
                    "filename": filename,
                    "entities": file_entities
                })
                all_unique_entities.update(file_entities)
    
    if not all_unique_entities:
        return "No legal entities found in playbook."
    
    # Build human-readable summary
    summary = f"## Playbook Legal Entities ({len(all_unique_entities)} unique)\n\n"
    
    for idx, file_data in enumerate(entities_by_file, 1):
        filename = file_data["filename"]
        entities = file_data["entities"]
        summary += f"### File {idx}: {filename}\n"
        summary += f"**Entities ({len(entities)})**:  {', '.join(entities[:10])}"
        if len(entities) > 10:
            summary += f" ... (and {len(entities) - 10} more)"
        summary += "\n\n"
    
    summary += f"### All Unique Legal Entities\n"
    unique_list = sorted(list(all_unique_entities))
    summary += ", ".join(unique_list)
    
    # Store for later use
    tool_context.state["researcher:targets"] = unique_list
    tool_context.state["researcher:files"] = entities_by_file
    
    return summary

async def save_compliance_updates(tool_context: ToolContext, compliance_json: str) -> str:
    """
    Saves the researched compliance updates to 'compliance_updates.json'.
    Args:
        compliance_json: The JSON string containing the findings.
    """
    try:
        # Validate JSON
        parsed = json.loads(compliance_json)
        
        # Save to file
        filename = "compliance_updates.json"
        with open(filename, "w") as f:
            json.dump(parsed, f, indent=4)
            
        return f"Success: Compliance updates saved to {filename}"
        
    except json.JSONDecodeError:
        return "Error: Invalid JSON format provided."
    except Exception as e:
        return f"Error saving file: {str(e)}"
