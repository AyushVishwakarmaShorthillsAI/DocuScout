from typing import List
import json
import os
import PyPDF2
from google.adk.tools.tool_context import ToolContext

async def fetch_audit_context(tool_context: ToolContext) -> str:
    """
    Loads the dynamic_playbook.json and compliance_updates.json to prepare for audit.
    Returns a human-readable summary of both datasets organized by filename.
    """
    
    # 1. Load Dynamic Playbook (Contract Clauses)
    playbook_data = tool_context.state.get("clausehunter:playbook")
    if not playbook_data:
        try:
            with open("dynamic_playbook.json", "r") as f:
                playbook_data = json.load(f)
        except FileNotFoundError:
            return "Error: 'dynamic_playbook.json' not found. Run ClauseHunter first."
        except Exception as e:
            return f"Error reading playbook: {str(e)}"
    
    if not playbook_data:
        return "Error: Playbook is empty."
    
    # 2. Load Compliance Updates (Legal Research Results)
    try:
        with open("compliance_updates.json", "r") as f:
            compliance_data = json.load(f)
    except FileNotFoundError:
        return "Error: 'compliance_updates.json' not found. Run Researcher first."
    except Exception as e:
        return f"Error reading compliance updates: {str(e)}"
    
    if not compliance_data:
        return "Error: Compliance updates file is empty."
    
    # Build human-readable summary
    summary = "## Audit Context Loaded\n\n"
    
    # Parse Playbook (New Structure: {"playbook": [{"filename": "...", "legal_entities": [...]}]})
    summary += "### Contract Playbook (What's in the documents)\n\n"
    playbook_files = {}
    
    if isinstance(playbook_data, dict) and "playbook" in playbook_data:
        for entry in playbook_data.get("playbook", []):
            if isinstance(entry, dict):
                filename = entry.get("filename", "Unknown")
                entities = entry.get("legal_entities", [])
                playbook_files[filename] = entities
                
                summary += f"**{filename}**: {len(entities)} legal entities\n"
                if entities:
                    summary += f"  - {', '.join(entities[:5])}"
                    if len(entities) > 5:
                        summary += f" ... (and {len(entities) - 5} more)"
                    summary += "\n"
                summary += "\n"
    else:
        return "Error: Unexpected playbook format. Expected new structure with 'playbook' key."
    
    # Parse Compliance Updates (New Structure: [{"filename": "...", "laws": [{"law_name": "...", ...}]}])
    summary += "### Compliance Updates (Legal research findings)\n\n"
    compliance_files = {}
    
    if isinstance(compliance_data, list):
        for entry in compliance_data:
            if isinstance(entry, dict):
                filename = entry.get("filename", "Unknown")
                laws = entry.get("laws", [])
                compliance_files[filename] = laws
                
                summary += f"**{filename}**: {len(laws)} laws researched\n"
                for law in laws[:3]:  # Show first 3
                    law_name = law.get("law_name", "Unknown")
                    status = law.get("status", "Unknown")
                    summary += f"  - {law_name}: {status}\n"
                if len(laws) > 3:
                    summary += f"  ... (and {len(laws) - 3} more)\n"
                summary += "\n"
    else:
        return "Error: Unexpected compliance format. Expected array of file entries."
    
    # Store in session state for later use
    tool_context.state["auditor:playbook_files"] = playbook_files
    tool_context.state["auditor:compliance_files"] = compliance_files
    
    summary += "---\n\n"
    summary += f"**Ready for Audit**: {len(playbook_files)} contract files loaded, {len(compliance_files)} compliance reports available.\n"
    
    return summary

async def fetch_law_context_from_document(tool_context: ToolContext, law_name: str, filename: str) -> str:
    """
    Opens the specific document and finds the paragraph/sentence where the law is mentioned.
    This provides the 'Contextual Re-Fetch' needed to verify compliance.
    
    Args:
        law_name: The name of the law to find (e.g., "Minimum Wages Act").
        filename: The specific PDF filename (e.g., "Contract.pdf").
    
    Returns:
        Human-readable string with context snippets where the law is mentioned.
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
                extracted_context.append(f"**Page {i+1}**: ...{snippet}...")
                
        if not extracted_context:
            return f"Law '{law_name}' not found in the text of '{filename}'."
            
        result = f"## Context for '{law_name}' in '{filename}'\n\n"
        result += "\n\n".join(extracted_context)
        return result

    except Exception as e:
        return f"Error reading PDF: {str(e)}"

async def save_audit_report(tool_context: ToolContext, report_md: str) -> str:
    """
    Saves the final 'risk_audit_report.md'.
    
    Args:
        report_md: The markdown content of the audit report.
        
    Returns:
        Success or error message.
    """
    filename = "risk_audit_report.md"
    try:
        with open(filename, "w") as f:
            f.write(report_md)
        return f"Success: Audit report saved to {filename}"
    except Exception as e:
        return f"Error saving report: {str(e)}"

async def fetch_all_laws_from_file(tool_context: ToolContext, filename: str, law_names: List[str]) -> str:
    """
    BATCH VERSION: Searches for multiple laws in a single document at once.
    This is much more efficient than calling fetch_law_context_from_document multiple times.
    
    Args:
        filename: The PDF filename to search in.
        law_names: List of law names to search for (e.g., ["Minimum Wages Act", "ESI Act"]).
    
    Returns:
        Human-readable string with context for ALL laws found in the document.
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
    
    # Read entire PDF once
    try:
        reader = PyPDF2.PdfReader(file_path)
        page_texts = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                page_texts.append((i+1, text))
        
        if not page_texts:
            return f"Error: Could not extract text from '{filename}'."
        
        # Search for each law
        results = []
        results.append(f"## Batch Law Context Search in '{filename}'\n\n")
        results.append(f"Searching for {len(law_names)} laws...\n\n")
        
        for law_name in law_names:
            law_found = False
            law_contexts = []
            
            for page_num, text in page_texts:
                if law_name.lower() in text.lower():
                    law_found = True
                    # Extract context
                    start_idx = text.lower().find(law_name.lower())
                    start = max(0, start_idx - 150)
                    end = min(len(text), start_idx + 250)
                    snippet = text[start:end].replace("\n", " ")
                    law_contexts.append(f"  - **Page {page_num}**: ...{snippet}...")
            
            if law_found:
                results.append(f"### ✅ {law_name}\n")
                results.append("\n".join(law_contexts))
                results.append("\n\n")
            else:
                results.append(f"### ❌ {law_name}\n")
                results.append(f"Not found in document.\n\n")
        
        return str("".join(results))
        
    except Exception as e:
        return f"Error reading PDF: {str(e)}"
