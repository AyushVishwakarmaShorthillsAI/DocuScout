from google.adk.tools.tool_context import ToolContext
import json

async def fetch_raw_extraction_results(tool_context: ToolContext) -> str:
    """
    Fetches the raw results from all ClauseHunter subagents (Gliner, LexNLP, RAG)
    and returns them as a human-readable summary organized by filename.
    
    Args:
        tool_context: The execution context containing session state.
        
    Returns:
        Human-readable string summary of extraction results organized by file.
    """
    gliner_res = tool_context.state.get("clausehunter:gliner", {})
    lexnlp_res = tool_context.state.get("clausehunter:lexnlp", {})
    rag_res = tool_context.state.get("clausehunter:rag", "")
    
    # Build a readable summary organized by filename
    summary = "## Document Extraction Results\n\n"
    summary += "**IMPORTANT**: Use the EXACT filenames shown below in your playbook JSON.\n\n"
    
    # Get all unique filenames from both sources
    all_filenames = set()
    if gliner_res:
        all_filenames.update(gliner_res.keys())
    if lexnlp_res:
        all_filenames.update(lexnlp_res.keys())
    
    if not all_filenames:
        summary += "No extraction results available.\n"
        return summary
    
    # Process each file
    for idx, filename in enumerate(sorted(all_filenames), 1):
        summary += f"### File {idx}: `{filename}`\n\n"
        
        # GLiNER entities for this file
        file_entities = []
        if filename in gliner_res and isinstance(gliner_res[filename], list):
            for entity in gliner_res[filename]:
                if isinstance(entity, dict) and "text" in entity:
                    file_entities.append(entity["text"])
        
        # LexNLP acts for this file
        if filename in lexnlp_res and isinstance(lexnlp_res[filename], dict):
            acts = lexnlp_res[filename].get('acts', [])
            if isinstance(acts, list):
                file_entities.extend(acts)
        
        # Deduplicate and display
        unique_entities = sorted(list(set(file_entities)))
        if unique_entities:
            # Limit display to first 20 entities
            display_entities = unique_entities[:20]
            summary += f"**Legal Entities Found ({len(unique_entities)} total)**:\n"
            summary += ", ".join(display_entities)
            if len(unique_entities) > 20:
                summary += f" ... (and {len(unique_entities) - 20} more)"
            summary += "\n\n"
        else:
            summary += "No entities found in this file.\n\n"
    
    # RAG Summary (applies to all documents)
    if rag_res and isinstance(rag_res, str) and rag_res.strip():
        summary += "### Additional Context (RAG Analysis)\n\n"
        if len(rag_res) > 800:
            summary += rag_res[:800] + "...\n\n"
        else:
            summary += rag_res + "\n\n"
    
    summary += "---\n\n"
    summary += "**Instructions**: Create a playbook JSON using the EXACT filenames shown above (e.g., `LeaseOffice.pdf`, not `document1.pdf`).\n"
    
    return summary

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
