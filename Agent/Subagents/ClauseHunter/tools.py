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

    # DEBUG: Save payload to disk for inspection
    try:
        debug_path = os.path.join("DB", "debug_clausehunter_payload.json") # Save in DB so it's visible easily
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, indent=2, default=str)
        logger.info(f"[ClauseHunter Tools] 🐞 Saved debug payload to {debug_path}")
    except Exception as e:
        logger.error(f"[ClauseHunter Tools] ❌ Failed to save debug payload: {e}")
    
    # Final Safety Net: Hard Truncate if still massive
    # --- CONVERT TO MARKDOWN SUMMARY (Sanitization) ---
    logger.info("[ClauseHunter Tools] 🔄 Converting payload to Markdown to avoid Safety/Size errors...")
    
    lines = ["**Extraction Results Summary**\n"]
    
    # helper to recursively print dicts/lists
    def dict_to_lines(d, indent=0):
        res = []
        prefix = "  " * indent
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, (list, set)):
                    if v:
                        res.append(f"{prefix}- **{k}**:")
                        for item in v:
                            res.append(f"{prefix}  - {item}")
                elif isinstance(v, dict):
                    res.append(f"{prefix}- **{k}**:")
                    res.extend(dict_to_lines(v, indent + 1))
                else:
                    res.append(f"{prefix}- **{k}**: {v}")
        return res

    lines.append("### Gliner Entities")
    lines.extend(dict_to_lines(compressed_gliner))
    
    lines.append("\n### LexNLP Entities")
    lines.extend(dict_to_lines(simplified_lexnlp))
    
    lines.append("\n### RAG Context")
    # Truncate RAG if too long (safe limit)
    rag_text = str(rag_res)
    if len(rag_text) > 5000:
        rag_text = rag_text[:5000] + "... [TRUNCATED]"
    lines.append(rag_text)
    
    final_output = "\n".join(lines)
    
    # Save the MARKDOWN debug payload
    try:
        debug_md_path = os.path.join("DB", "debug_clausehunter_payload.md")
        with open(debug_md_path, "w", encoding="utf-8") as f:
            f.write(final_output)
        logger.info(f"[ClauseHunter Tools] 🐞 Saved debug Markdown payload to {debug_md_path}")
    except Exception:
        pass

    # Final Safety Check: Length
    if len(final_output) > 25000:
         logger.warning(f"[ClauseHunter Tools] ⚠️  Markdown too large ({len(final_output)} chars), truncating.")
         return final_output[:25000] + "\n... [TRUNCATED]"
    
    elapsed = time.time() - function_start
    logger.info(f"[ClauseHunter Tools] ✅ fetch_raw_extraction_results completed in {elapsed:.2f}s")
    return final_output

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

async def export_playbook_to_disk(tool_context: ToolContext, output_filename: str = "dynamic_playbook.json") -> str:
    """
    Reads the 'clausehunter:playbook' from session state and writes it to a local JSON file.
    
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
    
    if not playbook_data:
        logger.error("[ClauseHunter Tools] ❌ No playbook found in session state. Cannot export.")
        return "Error: No playbook found in session state. Please run ClauseFinder to generate it first."
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
