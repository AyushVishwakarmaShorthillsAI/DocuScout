from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.tools.tool_context import ToolContext

async def run_rag_extraction_on_db(tool_context: ToolContext, query_focus: str = "legal clauses and terms") -> str:
    """
    Uses Google File Search (RAG) to extract key legal clauses from the documents.
    It expects the documents to be already ingested into 'DocuScout Store' by FileReader.
    
    Args:
        query_focus: What to focus the extraction on. Defaults to "legal clauses and terms".
        
    Returns:
        Extracted insights from the LLM.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found."
    
    client = genai.Client(api_key=api_key)
    
    # 1. Find the store
    target_store = None
    try:
        stores = list(client.file_search_stores.list())
        for store in stores:
            if store.display_name == 'DocuScout Store':
                target_store = store
                break
        
        if not target_store:
            return "Error: 'DocuScout Store' not found. Please run FileReader first."
            
    except Exception as e:
        return f"Error connecting to File Search: {e}"

    # 2. Run extraction query
    prompt = f"""
    Analyze the documents in the store. 
    Identify key information regarding {query_focus} and specific legal entities.

    Focus your search and extraction on the following key identifiers and terms:
    1. Constitutional/Statutory: Article, Section, Schedule, Constitution, Act
    2. Legal Provisions: Provision, Clause, Rule, Regulation, Explanation, Proviso
    3. Specific Statutes: IPC, CrPC, Evidence Act, Contract Act, Companies Act, NI Act
    4. Key Concepts: Punishment, Penalty, Imprisonment, Notwithstanding (Non-obstante)
    
    Instructions:
    1. Synthesize the findings into a concise summary.
    2. Do NOT use long verbatim quotes. Paraphrase the content logic.
    3. Identify specific occurrences of the above terms (e.g. "Section 138 of NI Act") and summarize their context.
    4. If specific clauses are found, describe their effect rather than reciting them.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[target_store.name]
                        )
                    )
                ]
            )
        )
        if response.text:
            tool_context.state["clausehunter:rag"] = response.text
            return "RAG extraction complete. Insights saved to session state."
        else:
            return f"Error: No text in response. Raw response: {response}"
    except Exception as e:
        return f"Error generating content: {e}"
