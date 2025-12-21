import json
import os
import time
import logging
import PyPDF2
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

async def fetch_audit_context(tool_context: ToolContext) -> str:
    """
    Reads the 'dynamic_playbook.json' (Contract Clauses) and 'compliance_updates.json' (Ground Truth).
    Returns a summary of both datasets to begin the audit.
    """
    function_start = time.time()
    logger.info("=" * 100)
    logger.info(f"[Critic Tools] 🔍 fetch_audit_context() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    context_str = "--- AUDIT CONTEXT ---\n\n"
    
    # 1. Load Compliance Updates (Ground Truth)
    logger.info("[Critic Tools] 📖 Step 1: Loading compliance_updates.json (Ground Truth)...")
    try:
        compliance_start = time.time()
        with open("compliance_updates.json", "r") as f:
            compliance_data = json.load(f)
        compliance_elapsed = time.time() - compliance_start
        
        updates = compliance_data.get("updates", [])
        logger.info(f"[Critic Tools] ✅ Loaded compliance_updates.json in {compliance_elapsed:.2f}s")
        logger.info(f"[Critic Tools] 📊 Found {len(updates)} compliance update entries")
        
        context_str += f"GROUND TRUTH (Legal Updates): Found {len(updates)} entries.\n"
        for idx, u in enumerate(updates[:5]):  # Log first 5
            logger.debug(f"[Critic Tools]   Entry {idx+1}: {u.get('law')} - {u.get('status')}")
            context_str += f"- {u.get('law')}: {u.get('status')}\n"
        if len(updates) > 5:
            logger.debug(f"[Critic Tools]   ... and {len(updates) - 5} more entries")
    except FileNotFoundError:
        logger.error("[Critic Tools] ❌ compliance_updates.json not found")
        return "Error: 'compliance_updates.json' not found. Run Researcher first."
    except Exception as e:
        logger.error(f"[Critic Tools] ❌ Error loading compliance_updates.json: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[Critic Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error loading compliance updates: {str(e)}"
        
    context_str += "\n"

    # 2. Load Contract Playbook (Subject)
    logger.info("[Critic Tools] 📖 Step 2: Loading dynamic_playbook.json (Subject Contract)...")
    # We try session state first, then disk
    playbook_data = tool_context.state.get("clausehunter:playbook")
    if playbook_data:
        logger.info("[Critic Tools] ✅ Found playbook in session state")
    else:
        logger.info("[Critic Tools] ⚠️  Playbook not in session state, trying disk...")
        if not playbook_data:
            try:
                playbook_start = time.time()
                with open("dynamic_playbook.json", "r") as f:
                    playbook_data = json.load(f)
                playbook_elapsed = time.time() - playbook_start
                logger.info(f"[Critic Tools] ✅ Loaded dynamic_playbook.json from disk in {playbook_elapsed:.2f}s")
            except FileNotFoundError:
                logger.error("[Critic Tools] ❌ dynamic_playbook.json not found")
                return "Error: 'dynamic_playbook.json' not found. Run ClauseHunter first."
            except Exception as e:
                logger.error(f"[Critic Tools] ❌ Error loading dynamic_playbook.json: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"[Critic Tools] 📋 Traceback:\n{traceback.format_exc()}")
                return f"Error loading playbook: {str(e)}"
            
    if not playbook_data:
        logger.error("[Critic Tools] ❌ Playbook is empty")
        return "Error: Playbook is empty."
    
    # Handle new playbook structure (with "playbook" key) or old structure
    logger.info(f"[Critic Tools] 🔍 Analyzing playbook structure (type: {type(playbook_data).__name__})...")
    
    if isinstance(playbook_data, dict) and "playbook" in playbook_data:
        # New structure: {"playbook": [{"clause_name": "...", "source_documents": [...], ...}]}
        logger.info("[Critic Tools] 📋 Detected new playbook structure (with 'playbook' key)")
        clauses = playbook_data.get("playbook", [])
        logger.info(f"[Critic Tools] 📊 Found {len(clauses)} clauses in playbook")
        
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
        
        logger.info(f"[Critic Tools] 📁 Grouped into {len(doc_to_clauses)} source documents")
        context_str += f"Subject Contract: Found {len(doc_to_clauses)} files with {len(clauses)} clauses.\n"
        for filename, clause_names in doc_to_clauses.items():
            logger.debug(f"[Critic Tools]   File: {filename} - {len(clause_names)} clauses")
            context_str += f"- File: {filename} contains {len(clause_names)} clauses: {', '.join(clause_names[:5])}"
            if len(clause_names) > 5:
                context_str += f" (and {len(clause_names) - 5} more)"
            context_str += "\n"
            
    elif isinstance(playbook_data, dict):
        # Old structure: {"filename": {"laws": [...], "acts": [...]}}
        logger.info("[Critic Tools] 📋 Detected old playbook structure (filename-based)")
        logger.info(f"[Critic Tools] 📊 Found {len(playbook_data)} files in playbook")
        context_str += f"Subject Contract: Found {len(playbook_data)} files.\n"
        for filename, content in playbook_data.items():
            if isinstance(content, dict):
                laws = [x.get('text', x) if isinstance(x, dict) else x for x in content.get('laws', [])]
                logger.debug(f"[Critic Tools]   File: {filename} - {len(laws)} laws")
                context_str += f"- File: {filename} contains laws: {', '.join(laws[:5])}\n"
            elif isinstance(content, list):
                # Handle if content is a list
                clause_names = [item.get('clause_name', item.get('name', str(item))) if isinstance(item, dict) else str(item) for item in content[:5]]
                logger.debug(f"[Critic Tools]   File: {filename} - {len(content)} items")
                context_str += f"- File: {filename} contains: {', '.join(clause_names)}\n"
    else:
        logger.error(f"[Critic Tools] ❌ Unexpected playbook format: {type(playbook_data)}")
        return f"Error: Unexpected playbook format. Expected dict, got {type(playbook_data)}"
    
    elapsed = time.time() - function_start
    context_length = len(context_str)
    logger.info(f"[Critic Tools] ✅ fetch_audit_context completed in {elapsed:.2f}s")
    logger.info(f"[Critic Tools] 📊 Context string length: {context_length} characters")
    logger.info("=" * 100)
        
    return context_str

async def fetch_law_context_from_document(tool_context: ToolContext, law_name: str, filename: str) -> str:
    """
    Opens the specific document and finds the paragraph/sentence where the law is mentioned.
    This provides the 'Contextual Re-Fetch' needed to verify compliance.
    
    Args:
        law_name: The name of the law to find (e.g., "Minimum Wages Act").
        filename: The specific PDF filename (e.g., "Contract.pdf").
    """
    function_start = time.time()
    logger.info(f"[Critic Tools] 🔍 fetch_law_context_from_document() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[Critic Tools] 📥 Parameters: law_name='{law_name}', filename='{filename}'")
    
    # Construct path: Check 'DB', 'input_pdfs', and current dir
    potential_paths = [
        os.path.join("DB", filename),
        os.path.join("input_pdfs", filename),
        filename
    ]
    
    logger.info(f"[Critic Tools] 🔍 Searching for file in paths: {potential_paths}")
    file_path = None
    for p in potential_paths:
        if os.path.exists(p):
            file_path = p
            logger.info(f"[Critic Tools] ✅ Found file at: {file_path}")
            break
            
    if not file_path:
        logger.error(f"[Critic Tools] ❌ File '{filename}' not found in any of the paths")
        return f"Error: File '{filename}' not found in DB, input_pdfs, or current directory."
            
    extracted_context = []
    
    try:
        logger.info(f"[Critic Tools] 📄 Opening PDF: {file_path}")
        pdf_start = time.time()
        reader = PyPDF2.PdfReader(file_path)
        num_pages = len(reader.pages)
        logger.info(f"[Critic Tools] 📊 PDF has {num_pages} pages")
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text: 
                continue
                
            # Simple keyword search (Case Insensitive)
            if law_name.lower() in text.lower():
                logger.info(f"[Critic Tools] ✅ Found '{law_name}' on page {i+1}")
                # Extract the specific paragraph (Naive splitting by newline or period)
                # For better context, we get the surrounding characters
                start_idx = text.lower().find(law_name.lower())
                # Grab 200 chars before and after
                start = max(0, start_idx - 200)
                end = min(len(text), start_idx + 300)
                snippet = text[start:end].replace("\n", " ")
                extracted_context.append(f"Page {i+1}: ...{snippet}...")
                logger.debug(f"[Critic Tools]   Extracted snippet length: {len(snippet)} chars")
        
        pdf_elapsed = time.time() - pdf_start
        elapsed = time.time() - function_start
        
        if not extracted_context:
            logger.warning(f"[Critic Tools] ⚠️  Law '{law_name}' not found in '{filename}'")
            return f"Law '{law_name}' not found in the text of '{filename}'."
        
        logger.info(f"[Critic Tools] ✅ Found {len(extracted_context)} occurrences of '{law_name}' in {pdf_elapsed:.2f}s")
        logger.info(f"[Critic Tools] ⏱️  Total function time: {elapsed:.2f}s")
            
        return f"Context for '{law_name}' in '{filename}':\n" + "\n".join(extracted_context)

    except Exception as e:
        elapsed = time.time() - function_start
        logger.error(f"[Critic Tools] ❌ Error reading PDF after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[Critic Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error reading PDF: {str(e)}"

async def save_audit_report(tool_context: ToolContext, report_md: str) -> str:
    """
    Saves the final 'risk_audit_report.md'.
    """
    function_start = time.time()
    filename = "risk_audit_report.md"
    logger.info(f"[Critic Tools] 💾 save_audit_report() called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[Critic Tools] 📥 Report markdown length: {len(report_md)} characters")
    
    try:
        write_start = time.time()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_md)
        write_elapsed = time.time() - write_start
        
        file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
        elapsed = time.time() - function_start
        
        logger.info(f"[Critic Tools] ✅ Successfully saved {filename}")
        logger.info(f"[Critic Tools] 📊 File size: {file_size} bytes")
        logger.info(f"[Critic Tools] ⏱️  Write time: {write_elapsed:.2f}s, Total: {elapsed:.2f}s")
        logger.info("=" * 100)
        
        return f"Success: Audit report saved to {filename}"
    except Exception as e:
        elapsed = time.time() - function_start
        logger.error(f"[Critic Tools] ❌ Error saving report after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"[Critic Tools] 📋 Traceback:\n{traceback.format_exc()}")
        return f"Error saving report: {str(e)}"
