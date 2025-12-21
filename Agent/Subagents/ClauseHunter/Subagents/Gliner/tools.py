from gliner import GLiNER
from PyPDF2 import PdfReader
import glob
import os

from google.adk.tools.tool_context import ToolContext

async def run_gliner_on_db(tool_context: ToolContext, db_path: str = "DB") -> str:
    """
    Runs GLiNER extraction on all PDF files in the DB directory.
    
    Args:
        db_path: Path to the directory containing PDF files. Defaults to "DB".
        
    Returns:
        A JSON string containing extracted entities from all files.
    """
    print(f"Loading GLiNER model...")
    # Using the medium model for better performance/size balance
    try:
        model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
    except Exception as e:
        return f"Error loading GLiNER model: {e}"

    entity_labels = [
        "statute", "act", "provision", "section", 
        "article", "clause", "regulation", "rule", 
        "code", "law", "ordinance", "amendment"
    ]
    
    pdf_files = glob.glob(os.path.join(db_path, "*.pdf"))
    if not pdf_files:
        return "No PDF files found in DB directory."

    results = {}
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        print(f"Processing {filename} with GLiNER...")
        try:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            entities = model.predict_entities(text, entity_labels, threshold=0.5)
            
            file_entities = []
            for entity in entities:
                file_entities.append({
                    "text": entity["text"],
                    "label": entity["label"],
                    "score": round(entity["score"], 3)
                })
            
            results[filename] = file_entities
            
        except Exception as e:
            results[filename] = {"error": str(e)}

    tool_context.state["clausehunter:gliner"] = results
    return f"GLiNER extraction complete. Processed {len(pdf_files)} files. Raw results saved to session state."
