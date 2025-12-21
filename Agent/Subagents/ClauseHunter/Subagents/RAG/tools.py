from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

from google.adk.tools.tool_context import ToolContext

async def run_rag_extraction_on_db(tool_context: ToolContext, query_focus: str = "legal clauses and terms") -> str:
    """
    Uses Google File Search (RAG) to extract key legal clauses from the documents.
    NOTE: This requires documents to be ingested into 'DocuScout Store' by FileReader.
    If the store contains old/irrelevant documents, RAG may return incorrect information.
    
    Args:
        query_focus: What to focus the extraction on. Defaults to "legal clauses and terms".
        
    Returns:
        Extracted insights from the LLM, or empty string if store not found/error.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Return empty string instead of error to allow other extractors to work
        tool_context.state["clausehunter:rag"] = ""
        return "Warning: GEMINI_API_KEY not found. Skipping RAG extraction."
    
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
            # Return empty string instead of error - RAG is optional
            tool_context.state["clausehunter:rag"] = ""
            return "Warning: 'DocuScout Store' not found. Skipping RAG extraction. Please run FileReader first to ingest current documents."
            
    except Exception as e:
        tool_context.state["clausehunter:rag"] = ""
        return f"Warning: Error connecting to File Search: {e}. Skipping RAG extraction."

    # 2. Run extraction query with strict instructions to only use current document
    prompt = f"""
    Analyze ONLY the documents currently in the store. 
    Identify key information regarding {query_focus} and specific legal entities.

    IMPORTANT: Only extract information that is EXPLICITLY mentioned in the documents.
    Do NOT infer, assume, or add information that is not present in the source documents.

    Focus your search and extraction on the following key identifiers and terms:
    1. Constitutional/Statutory: Article, Section, Schedule, Constitution, Act
    2. Legal Provisions: Provision, Clause, Rule, Regulation, Explanation, Proviso
    3. Specific Statutes: IPC, CrPC, Evidence Act, Contract Act, Companies Act, NI Act
    4. Key Concepts: Punishment, Penalty, Imprisonment, Notwithstanding (Non-obstante)
    
    Instructions:
    1. ONLY extract entities that are explicitly mentioned in the documents.
    2. If an entity is not found, do NOT include it in your response.
    3. Synthesize the findings into a concise summary.
    4. Do NOT use long verbatim quotes. Paraphrase the content logic.
    5. Identify specific occurrences of the above terms (e.g. "Section 138 of NI Act") and summarize their context.
    6. If specific clauses are found, describe their effect rather than reciting them.
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
        # Handle empty responses gracefully
        if response and hasattr(response, 'text') and response.text:
            tool_context.state["clausehunter:rag"] = response.text
            return "RAG extraction complete. Insights saved to session state."
        else:
            # Empty response - return empty string instead of error
            tool_context.state["clausehunter:rag"] = ""
            return "Warning: RAG returned empty response. Skipping RAG extraction."
    except Exception as e:
        # Return empty string on error to allow other extractors to work
        tool_context.state["clausehunter:rag"] = ""
        return f"Warning: Error generating RAG content: {e}. Skipping RAG extraction."
