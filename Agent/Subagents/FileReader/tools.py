from google import genai
from google.genai import types
import time
import glob
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_documents(folder_path: str = "DB") -> str:
    """
    Ingests PDF documents from the specified folder into a Google File Search Store.
    
    Args:
        folder_path: The path to the folder containing PDF files. Defaults to "Docs".
        
    Returns:
        The name of the created File Search Store.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."
    
    client = genai.Client(api_key=api_key)
    
    # Check for existing File Search Store
    file_search_store = None
    try:
        stores = list(client.file_search_stores.list())
        for store in stores:
            if store.display_name == 'DocuScout Store':
                file_search_store = store
                print(f"Using existing File Search Store: {file_search_store.name}")
                break
        
        if not file_search_store:
            file_search_store = client.file_search_stores.create(
                config={'display_name': 'DocuScout Store'}
            )
            print(f"Created File Search Store: {file_search_store.name}")
            
    except Exception as e:
        return f"Failed to get or create File Search Store: {e}"

    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        return "No PDF files found in the specified directory."

    for pdf_file in pdf_files:
        print(f"Uploading {pdf_file}...")
        try:
            operation = client.file_search_stores.upload_to_file_search_store(
                file=pdf_file,
                file_search_store_name=file_search_store.name,
                config={'display_name': os.path.basename(pdf_file)}
            )
            
            while not operation.done:
                time.sleep(2)
                operation = client.operations.get(operation)
                
            print(f"Uploaded {pdf_file}")
        except Exception as e:
            print(f"Failed to upload {pdf_file}: {e}")

    return f"Successfully created store: {file_search_store.name} and uploaded {len(pdf_files)} documents."
