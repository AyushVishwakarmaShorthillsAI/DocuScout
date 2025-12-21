from google.adk.tools.tool_context import ToolContext
import json
import os
import time
import logging

logger = logging.getLogger(__name__)

async def fetch_raw_extraction_results(tool_context: ToolContext) -> str:
    """
    Fetches the raw results from all ClauseHunter subagents (Gliner, LexNLP, RAG)
    from the session state to allow the Agent to analyze and filter them.
    
    Args:
        tool_context: The execution context containing session state.
        
    Returns:
        JSON string containing the raw outputs from all subagents.
    """
    function_start = time.time()
    logger.info(f"[ClauseHunter Tools] 🔍 fetch_raw_extraction_results() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info("[ClauseHunter Tools] 📖 Reading results from session state...")
    gliner_res = tool_context.state.get("clausehunter:gliner", {})
    lexnlp_res = tool_context.state.get("clausehunter:lexnlp", {})
    rag_res = tool_context.state.get("clausehunter:rag", "")
    
    gliner_size = len(str(gliner_res)) if gliner_res else 0
    lexnlp_size = len(str(lexnlp_res)) if lexnlp_res else 0
    rag_size = len(str(rag_res)) if rag_res else 0
    
    logger.info(f"[ClauseHunter Tools] 📊 Session state data sizes:")
    logger.info(f"[ClauseHunter Tools]   - GLiNER: {gliner_size} chars ({'present' if gliner_res else 'empty'})")
    logger.info(f"[ClauseHunter Tools]   - LexNLP: {lexnlp_size} chars ({'present' if lexnlp_res else 'empty'})")
    logger.info(f"[ClauseHunter Tools]   - RAG: {rag_size} chars ({'present' if rag_res else 'empty'})")
    
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
    logger.info("[ClauseHunter Tools] 🔄 Serializing combined data to JSON...")
    dump_start = time.time()
    dumped = json.dumps(combined_data, default=str)
    dump_elapsed = time.time() - dump_start
    dumped_length = len(dumped)
    
    logger.info(f"[ClauseHunter Tools] ✅ JSON serialization completed in {dump_elapsed:.2f}s")
    logger.info(f"[ClauseHunter Tools] 📊 Serialized JSON length: {dumped_length} characters")
    
    # Drastic reduction to 10k chars to rule out size/timeout issues.
    if len(dumped) > 10000:
        logger.warning(f"[ClauseHunter Tools] ⚠️  JSON too large ({dumped_length} chars), truncating to 10000 chars")
        truncated = dumped[:10000] + "... [TRUNCATED - PLEASE FOCUS ON AVAILABLE DATA]"
        elapsed = time.time() - function_start
        logger.info(f"[ClauseHunter Tools] ⏱️  Function completed in {elapsed:.2f}s (truncated)")
        return truncated
    
    elapsed = time.time() - function_start
    logger.info(f"[ClauseHunter Tools] ✅ fetch_raw_extraction_results completed in {elapsed:.2f}s")
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
    function_start = time.time()
    logger.info(f"[ClauseHunter Tools] 💾 save_curated_playbook() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[ClauseHunter Tools] 📥 Input JSON length: {len(curated_playbook_json)} characters")
    
    try:
        # Validate JSON
        logger.info("[ClauseHunter Tools] 🔍 Validating JSON format...")
        parse_start = time.time()
        parsed = json.loads(curated_playbook_json)
        parse_elapsed = time.time() - parse_start
        logger.info(f"[ClauseHunter Tools] ✅ JSON valid, parsed in {parse_elapsed:.2f}s")
        
        if isinstance(parsed, dict):
            logger.info(f"[ClauseHunter Tools] 📊 Parsed structure: {type(parsed).__name__} with {len(parsed)} top-level keys")
        
        logger.info("[ClauseHunter Tools] 💾 Saving to session state 'clausehunter:playbook'...")
        tool_context.state["clausehunter:playbook"] = parsed
        
        elapsed = time.time() - function_start
        logger.info(f"[ClauseHunter Tools] ✅ Playbook saved to session state in {elapsed:.2f}s")
        
        return "Curated playbook successfully saved to session state."
    except json.JSONDecodeError as e:
        elapsed = time.time() - function_start
        logger.error(f"[ClauseHunter Tools] ❌ Invalid JSON format after {elapsed:.2f}s: {str(e)}")
        logger.error(f"[ClauseHunter Tools] 📋 JSON snippet (first 500 chars): {curated_playbook_json[:500]}")
        return "Error: Invalid JSON format provided."
    except Exception as e:
        elapsed = time.time() - function_start
        logger.error(f"[ClauseHunter Tools] ❌ Error saving playbook after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[ClauseHunter Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error saving playbook: {str(e)}"

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
    function_start = time.time()
    logger.info(f"[ClauseHunter Tools] 💾 export_playbook_to_disk() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[ClauseHunter Tools] 📥 Output filename: {output_filename}")
    
    logger.info("[ClauseHunter Tools] 🔍 Reading playbook from session state...")
    playbook_data = tool_context.state.get("clausehunter:playbook")
    
    # If no playbook exists, try to create fallback
    if not playbook_data:
        logger.warning("[ClauseHunter Tools] ⚠️  No playbook in session state, creating fallback...")
        fallback_start = time.time()
        fallback_result = await create_fallback_playbook(tool_context)
        fallback_elapsed = time.time() - fallback_start
        logger.info(f"[ClauseHunter Tools] 🔄 Fallback creation completed in {fallback_elapsed:.2f}s: {fallback_result}")
        
        playbook_data = tool_context.state.get("clausehunter:playbook")
        if not playbook_data:
            logger.error("[ClauseHunter Tools] ❌ Fallback creation failed, cannot export")
            return f"Error: {fallback_result}. Cannot export playbook."
    else:
        logger.info("[ClauseHunter Tools] ✅ Found playbook in session state")
    
    playbook_size = len(str(playbook_data)) if playbook_data else 0
    logger.info(f"[ClauseHunter Tools] 📊 Playbook data size: {playbook_size} characters")
    
    try:
        logger.info(f"[ClauseHunter Tools] 💾 Writing to {output_filename}...")
        write_start = time.time()
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(playbook_data, f, indent=4, default=str)
        write_elapsed = time.time() - write_start
        
        file_size = os.path.getsize(output_filename) if os.path.exists(output_filename) else 0
        elapsed = time.time() - function_start
        
        logger.info(f"[ClauseHunter Tools] ✅ Successfully exported playbook to {output_filename}")
        logger.info(f"[ClauseHunter Tools] 📊 File size: {file_size} bytes")
        logger.info(f"[ClauseHunter Tools] ⏱️  Write time: {write_elapsed:.2f}s, Total: {elapsed:.2f}s")
        
        return f"Successfully exported Dynamic Playbook to {output_filename}."
    except Exception as e:
        elapsed = time.time() - function_start
        logger.error(f"[ClauseHunter Tools] ❌ Error exporting file after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[ClauseHunter Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error exporting file: {str(e)}"
