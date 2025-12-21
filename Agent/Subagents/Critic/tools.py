import json
import os
import PyPDF2
from google.adk.tools.tool_context import ToolContext

async def fetch_audit_context(tool_context: ToolContext) -> str:
    """
    Reads the 'dynamic_playbook.json' (Contract Clauses) and 'compliance_updates.json' (Ground Truth).
    Returns a summary of both datasets to begin the audit.
    """
    context_str = "--- AUDIT CONTEXT ---\n\n"
    
    # 1. Load Compliance Updates (Ground Truth)
    try:
        with open("compliance_updates.json", "r") as f:
            compliance_data = json.load(f)
            updates = compliance_data.get("updates", [])
            context_str += f"GROUND TRUTH (Legal Updates): Found {len(updates)} entries.\n"
            for u in updates:
                context_str += f"- {u.get('law')}: {u.get('status')}\n"
    except FileNotFoundError:
        return "Error: 'compliance_updates.json' not found. Run Researcher first."
        
    context_str += "\n"

    # 2. Load Contract Playbook (Subject)
    # We try session state first, then disk
    playbook_data = tool_context.state.get("clausehunter:playbook")
    if not playbook_data:
        try:
            with open("dynamic_playbook.json", "r") as f:
                playbook_data = json.load(f)
        except FileNotFoundError:
            return "Error: 'dynamic_playbook.json' not found. Run ClauseHunter first."
            
    if not playbook_data:
         return "Error: Playbook is empty."
    
    # Handle new playbook structure (with "playbook" key) or old structure
    if isinstance(playbook_data, dict) and "playbook" in playbook_data:
        # New structure: {"playbook": [{"clause_name": "...", "source_documents": [...], ...}]}
        clauses = playbook_data.get("playbook", [])
        
        # Group clauses by source document
        doc_to_clauses = {}
        for clause in clauses:
            if isinstance(clause, dict):
                clause_name = clause.get("clause_name", "Unknown")
                source_docs = clause.get("source_documents", [])
                for doc in source_docs:
                    if doc not in doc_to_clauses:
                        doc_to_clauses[doc] = []
                    doc_to_clauses[doc].append(clause_name)
        
        context_str += f"Subject Contract: Found {len(doc_to_clauses)} files with {len(clauses)} clauses.\n"
        for filename, clause_names in doc_to_clauses.items():
            context_str += f"- File: {filename} contains {len(clause_names)} clauses: {', '.join(clause_names[:5])}"
            if len(clause_names) > 5:
                context_str += f" (and {len(clause_names) - 5} more)"
            context_str += "\n"
            
    elif isinstance(playbook_data, dict):
        # Old structure: {"filename": {"laws": [...], "acts": [...]}}
        context_str += f"Subject Contract: Found {len(playbook_data)} files.\n"
        for filename, content in playbook_data.items():
            if isinstance(content, dict):
                laws = [x.get('text', x) if isinstance(x, dict) else x for x in content.get('laws', [])]
                context_str += f"- File: {filename} contains laws: {', '.join(laws[:5])}\n"
            elif isinstance(content, list):
                # Handle if content is a list
                clause_names = [item.get('clause_name', item.get('name', str(item))) if isinstance(item, dict) else str(item) for item in content[:5]]
                context_str += f"- File: {filename} contains: {', '.join(clause_names)}\n"
    else:
        return f"Error: Unexpected playbook format. Expected dict, got {type(playbook_data)}"
        
    return context_str

async def fetch_law_context_from_document(tool_context: ToolContext, law_name: str, filename: str) -> str:
    """
    Opens the specific document and finds the paragraph/sentence where the law is mentioned.
    This provides the 'Contextual Re-Fetch' needed to verify compliance.
    
    Args:
        law_name: The name of the law to find (e.g., "Minimum Wages Act").
        filename: The specific PDF filename (e.g., "Contract.pdf").
    """
    # Construct path: Check 'DB', 'input_pdfs', and current dir
    potential_paths = [
        os.path.join("DB", filename),
        os.path.join("input_pdfs", filename),
        filename
    ]
    
    file_path = None
    for p in potential_paths:
        if os.path.exists(p):
            file_path = p
            break
            
    if not file_path:
        return f"Error: File '{filename}' not found in DB, input_pdfs, or current directory."
            
    extracted_context = []
    
    try:
        reader = PyPDF2.PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text: 
                continue
                
            # Simple keyword search (Case Insensitive)
            if law_name.lower() in text.lower():
                # Extract the specific paragraph (Naive splitting by newline or period)
                # For better context, we get the surrounding characters
                start_idx = text.lower().find(law_name.lower())
                # Grab 200 chars before and after
                start = max(0, start_idx - 200)
                end = min(len(text), start_idx + 300)
                snippet = text[start:end].replace("\n", " ")
                extracted_context.append(f"Page {i+1}: ...{snippet}...")
                
        if not extracted_context:
            return f"Law '{law_name}' not found in the text of '{filename}'."
            
        return f"Context for '{law_name}' in '{filename}':\n" + "\n".join(extracted_context)

    except Exception as e:
        return f"Error reading PDF: {str(e)}"

async def save_audit_report(tool_context: ToolContext, report_md: str) -> str:
    """
    Saves the final 'risk_audit_report.md'.
    """
    filename = "risk_audit_report.md"
    try:
        with open(filename, "w") as f:
            f.write(report_md)
        return f"Success: Audit report saved to {filename}"
    except Exception as e:
        return f"Error saving report: {str(e)}"
