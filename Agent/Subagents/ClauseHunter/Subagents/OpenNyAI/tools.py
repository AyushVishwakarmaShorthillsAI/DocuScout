import spacy
from PyPDF2 import PdfReader
import glob
import os
import sys
from dotenv import load_dotenv

from google.adk.tools.tool_context import ToolContext

load_dotenv()

# HuggingFace model repository for OpenNyAI
OPENNYAI_MODEL_REPO = "opennyaiorg/en_legal_ner_trf"

def _download_opennyai_model() -> str:
    """
    Downloads the OpenNyAI model from HuggingFace (similar to GLiNER's from_pretrained).
    Uses HuggingFace Hub to download and cache the model.
    
    Returns:
        Path to the downloaded model directory, or None if download failed.
    """
    try:
        from huggingface_hub import snapshot_download
        
        print(f"Downloading OpenNyAI model from HuggingFace: {OPENNYAI_MODEL_REPO}")
        print("This may take a few minutes on first use...")
        
        # snapshot_download automatically uses HF_HOME or ~/.cache/huggingface
        # It returns the path to the downloaded model
        model_path = snapshot_download(
            repo_id=OPENNYAI_MODEL_REPO,
            local_dir_use_symlinks=False
        )
        
        print(f"OpenNyAI model downloaded successfully to: {model_path}")
        return model_path
        
    except ImportError:
        print("Error: huggingface_hub not installed. Install it with: pip install huggingface_hub")
        return None
    except Exception as e:
        print(f"Error downloading OpenNyAI model: {e}")
        return None

def _get_opennyai_model_path() -> str:
    """
    Gets the OpenNyAI model path from environment variable, local cache, or downloads it.
    Similar to how GLiNER auto-finds/downloads models.
    
    Returns:
        Path to the model directory, or None if not found and download failed.
    """
    # 1. Check environment variable first (highest priority)
    model_path = os.getenv("OPENNYAI_MODEL_PATH")
    if model_path:
        # Expand user path if it contains ~
        model_path = os.path.expanduser(model_path)
        if os.path.exists(model_path):
            return model_path
    
    # 2. Check HuggingFace cache (where GLiNER stores models)
    try:
        from huggingface_hub import snapshot_download
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
        # HuggingFace stores models in: cache_dir/models--org--model_name/snapshots/hash/
        # We need to find the actual model directory
        hf_cache_path = os.path.join(cache_dir, "models--opennyaiorg--en_legal_ner_trf")
        if os.path.exists(hf_cache_path):
            # Find the latest snapshot
            snapshots_dir = os.path.join(hf_cache_path, "snapshots")
            if os.path.exists(snapshots_dir):
                snapshots = [d for d in os.listdir(snapshots_dir) if os.path.isdir(os.path.join(snapshots_dir, d))]
                if snapshots:
                    latest_snapshot = os.path.join(snapshots_dir, snapshots[-1])
                    if os.path.exists(latest_snapshot):
                        return latest_snapshot
    except:
        pass
    
    # 3. Try Spacy's model cache directory
    try:
        import spacy.util
        spacy_data_dir = spacy.util.find_user_data_dir()
        spacy_model_path = os.path.join(spacy_data_dir, "en_legal_ner_trf", "en_legal_ner_trf-3.2.0")
        if os.path.exists(spacy_model_path):
            return spacy_model_path
    except:
        pass
    
    # 4. Check relative to project root (common structure)
    current_file = os.path.abspath(__file__)
    project_root = current_file
    for _ in range(5):  # Go up 5 directory levels to reach project root
        project_root = os.path.dirname(project_root)
    
    relative_paths = [
        # Relative to project root
        os.path.join(project_root, "LawModels", "OpenNyAI", "en_legal_ner_model", "en_legal_ner_trf", "en_legal_ner_trf-3.2.0"),
        # Parent directory of project
        os.path.join(project_root, "..", "LawModels", "OpenNyAI", "en_legal_ner_model", "en_legal_ner_trf", "en_legal_ner_trf-3.2.0"),
        # Common desktop location
        os.path.join(os.path.expanduser("~"), "Desktop", "LawModels", "OpenNyAI", "en_legal_ner_model", "en_legal_ner_trf", "en_legal_ner_trf-3.2.0"),
        # Original hardcoded path (for backward compatibility)
        "/home/shtlp_0107/Desktop/LawModels/OpenNyAI/en_legal_ner_model/en_legal_ner_trf/en_legal_ner_trf-3.2.0",
    ]
    
    # 5. Check each path
    for path in relative_paths:
        normalized_path = os.path.normpath(path)
        if os.path.exists(normalized_path):
            return normalized_path
    
    # 6. If not found locally, try to download from HuggingFace (like GLiNER)
    print("OpenNyAI model not found locally. Attempting to download from HuggingFace...")
    downloaded_path = _download_opennyai_model()
    if downloaded_path:
        return downloaded_path
    
    return None

async def run_opennyai_on_db(tool_context: ToolContext, db_path: str = "DB") -> str:
    """
    Runs OpenNyAI extraction on all PDF files in the DB directory.
    Automatically downloads the model from HuggingFace if not found locally (like GLiNER).
    
    Args:
        db_path: Path to the directory containing PDF files. Defaults to "DB".
        
    Returns:
        A formatted string of extracted statutes and provisions.
    """
    print("Loading OpenNyAI model...")
    nlp = None
    
    # Try loading by name first (works if installed via 'spacy link' or opennyai package)
    try:
        nlp = spacy.load("en_legal_ner_trf")
        print("Found OpenNyAI model by name in Spacy cache")
    except:
        pass
    
    # If name loading failed, try auto-detection/download (like GLiNER)
    if nlp is None:
        model_path = _get_opennyai_model_path()
        if not model_path:
            error_msg = (
                "Error: OpenNyAI model not found and download failed.\n\n"
                "The model will be automatically downloaded from HuggingFace on first use.\n"
                "If download fails, you can:\n\n"
                "1. Set OPENNYAI_MODEL_PATH environment variable:\n"
                "   OPENNYAI_MODEL_PATH=/path/to/en_legal_ner_trf\n\n"
                "2. Install huggingface_hub: pip install huggingface_hub\n\n"
                "3. Or install opennyai package: pip install opennyai\n"
                "   Then use: spacy.load('en_legal_ner_trf')"
            )
            return error_msg
        
        try:
            print(f"Loading OpenNyAI model from: {model_path}")
            nlp = spacy.load(model_path)
            print("OpenNyAI model loaded successfully")
        except Exception as e:
            return f"Error loading OpenNyAI model from {model_path}: {e}"

    pdf_files = glob.glob(os.path.join(db_path, "*.pdf"))
    if not pdf_files:
        return "No PDF files found in DB directory."

    results = {}
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        print(f"Processing {filename} with OpenNyAI...")
        try:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            doc = nlp(text)
            
            statutes = []
            provisions = []
            
            for ent in doc.ents:
                if ent.label_ == 'STATUTE':
                    statutes.append(ent.text)
                elif ent.label_ == 'PROVISION':
                    provisions.append(ent.text)
            
            results[filename] = {
                "statutes": sorted(list(set(statutes))),
                "provisions": sorted(list(set(provisions)))
            }
            
        except Exception as e:
            results[filename] = {"error": str(e)}

    tool_context.state["clausehunter:opennyai"] = results
    return f"OpenNyAI extraction complete. Processed {len(pdf_files)} files. Raw results saved to session state."
