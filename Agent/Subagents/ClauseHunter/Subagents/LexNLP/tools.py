import lexnlp.extract.en.acts
from PyPDF2 import PdfReader
import glob
import os

from google.adk.tools.tool_context import ToolContext

async def run_lexnlp_on_db(tool_context: ToolContext, db_path: str = "DB") -> str:
    """
    Runs LexNLP extraction on all PDF files in the DB directory.
    
    Args:
        db_path: Path to the directory containing PDF files. Defaults to "DB".
        
    Returns:
        A string summary of extracted entities from all files.
    """
    pdf_files = glob.glob(os.path.join(db_path, "*.pdf"))
    if not pdf_files:
        return "No PDF files found in DB directory."

    results = {}
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        print(f"Processing {filename} with LexNLP...")
        try:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            file_data = {}
            
            # Extract Acts
            try:
                acts_list = list(lexnlp.extract.en.acts.get_acts(text))
                # Only keep the Act Name/Value, ignore location_start/end
                cleaned_acts = []
                for act in acts_list:
                    if isinstance(act, dict):
                        name = act.get("act_name") or act.get("value")
                        if name:
                            cleaned_acts.append(name)
                file_data['acts'] = sorted(list(set(cleaned_acts))) # Deduplicate
            except: file_data['acts'] = []                

            results[filename] = file_data
            
        except Exception as e:
            results[filename] = {"error": str(e)}

    # Save to local file
    try:
        with open("LexNLP_res.json", "w", encoding="utf-8") as f:
            import json
            json.dump(results, f, indent=4, default=str)
        print("Saved raw LexNLP results to LexNLP_res.json")
    except Exception as e:
        print(f"Error saving LexNLP_res.json: {e}")

    tool_context.state["clausehunter:lexnlp"] = results
    return f"LexNLP extraction complete. Processed {len(pdf_files)} files. Raw results saved to session state."
