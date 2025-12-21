from google.adk.tools.tool_context import ToolContext
import json

async def fetch_raw_extraction_results(tool_context: ToolContext) -> str:
    """
    Fetches the raw results from all ClauseHunter subagents (Gliner, LexNLP, RAG)
    from the session state to allow the Agent to analyze and filter them.
    
    Args:
        tool_context: The execution context containing session state.
        
    Returns:
        JSON string containing the raw outputs from all subagents.
    """
    gliner_res = tool_context.state.get("clausehunter:gliner", {})
    lexnlp_res = tool_context.state.get("clausehunter:lexnlp", {})
    rag_res = tool_context.state.get("clausehunter:rag", "")
    
    # Helper to compress entity lists: Group by Label
    def compress_entities(entity_list):
        if not isinstance(entity_list, list): return entity_list
        compressed = {}
        for item in entity_list:
            if isinstance(item, dict) and "text" in item and "label" in item:
                lbl = item["label"]
                txt = item["text"]
                if lbl not in compressed: compressed[lbl] = []
                if txt not in compressed[lbl]: compressed[lbl].append(txt)
        return compressed

    # Helper to simplify LexNLP output (strip locations)
    def simplify_lexnlp(res_dict):
        if not isinstance(res_dict, dict): return res_dict
        simplified = {}
        for filename, data in res_dict.items():
            file_simple = {}
            if isinstance(data, dict):
                for category, items in data.items(): # e.g. "acts": [...]
                   file_simple[category] = []
                   if isinstance(items, list):
                       for i in items:
                           # Extract meaningful text value
                           val = None
                           if isinstance(i, dict):
                               val = i.get("value") or i.get("act_name") or i.get("text")
                           elif isinstance(i, str):
                               val = i
                           
                           if val and val not in file_simple[category]:
                               file_simple[category].append(val)
                   elif isinstance(items, dict): # sometimes it's dict of dicts
                       pass 
            simplified[filename] = file_simple
        return simplified

    # 1. Compress GLiNER
    compressed_gliner = {}
    if isinstance(gliner_res, dict):
        for filename, entities in gliner_res.items():
            compressed_gliner[filename] = compress_entities(entities)

    # 2. Simplify LexNLP
    simplified_lexnlp = simplify_lexnlp(lexnlp_res)

    combined_data = {
        "summary_gliner": compressed_gliner,
        "summary_lexnlp": simplified_lexnlp,
        "raw_rag": rag_res
    }
    
    # Final Safety Net: Hard Truncate if still massive
    dumped = json.dumps(combined_data, default=str)
    # Drastic reduction to 10k chars to rule out size/timeout issues.
    if len(dumped) > 10000:
        return dumped[:10000] + "... [TRUNCATED - PLEASE FOCUS ON AVAILABLE DATA]"
    
    return dumped

async def save_curated_playbook(tool_context: ToolContext, curated_playbook_json: str) -> str:
    """
    Saves the LLM-curated, filtered, and deduplicated playbook JSON to the 'playbook' session state.
    
    Args:
        tool_context: The execution context.
        curated_playbook_json: The processed JSON string containing specific laws and clauses.
        
    Returns:
        Confirmation message.
    """
    try:
        # Validate JSON
        parsed = json.loads(curated_playbook_json)
        tool_context.state["clausehunter:playbook"] = parsed
        return "Curated playbook successfully saved to session state."
    except json.JSONDecodeError:
        return "Error: Invalid JSON format provided."

async def create_fallback_playbook(tool_context: ToolContext) -> str:
    """
    Creates a basic playbook directly from raw extraction results without LLM processing.
    This is a fallback when the LLM fails or returns empty responses.
    
    Args:
        tool_context: The execution context.
        
    Returns:
        Status message.
    """
    try:
        gliner_res = tool_context.state.get("clausehunter:gliner", {})
        lexnlp_res = tool_context.state.get("clausehunter:lexnlp", {})
        
        clauses = []
        
        # Extract from GLiNER
        if isinstance(gliner_res, dict):
            for filename, entities in gliner_res.items():
                if isinstance(entities, list):
                    for entity in entities:
                        if isinstance(entity, dict) and "text" in entity and "label" in entity:
                            clauses.append({
                                "name": entity["text"],
                                "type": entity["label"].title(),
                                "sources": ["GLiNER"],
                                "contexts": [f"Extracted from {filename}"]
                            })
        
        # Extract from LexNLP
        if isinstance(lexnlp_res, dict):
            for filename, data in lexnlp_res.items():
                if isinstance(data, dict):
                    for category, items in data.items():
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, str) and item:
                                    clauses.append({
                                        "name": item,
                                        "type": category.title(),
                                        "sources": ["LexNLP"],
                                        "contexts": [f"Extracted from {filename}"]
                                    })
        
        # Remove duplicates
        seen = set()
        unique_clauses = []
        for clause in clauses:
            key = (clause["name"], clause["type"])
            if key not in seen:
                seen.add(key)
                unique_clauses.append(clause)
        
        playbook_data = {"clauses": unique_clauses}
        tool_context.state["clausehunter:playbook"] = playbook_data
        return f"Fallback playbook created with {len(unique_clauses)} entities from raw extraction data."
    except Exception as e:
        return f"Error creating fallback playbook: {str(e)}"

async def export_playbook_to_disk(tool_context: ToolContext, output_filename: str = "dynamic_playbook.json") -> str:
    """
    Reads the 'clausehunter:playbook' from session state and writes it to a local JSON file.
    If no playbook exists, tries to create a fallback playbook from raw data.
    
    Args:
        tool_context: The execution context.
        output_filename: The filename to save to. Defaults to "dynamic_playbook.json".
        
    Returns:
        Status message indicating success or failure.
    """
    playbook_data = tool_context.state.get("clausehunter:playbook")
    
    # If no playbook exists, try to create fallback
    if not playbook_data:
        fallback_result = await create_fallback_playbook(tool_context)
        playbook_data = tool_context.state.get("clausehunter:playbook")
        if not playbook_data:
            return f"Error: {fallback_result}. Cannot export playbook."
        
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(playbook_data, f, indent=4, default=str)
        return f"Successfully exported Dynamic Playbook to {output_filename}."
    except Exception as e:
        return f"Error exporting file: {str(e)}"
