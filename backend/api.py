"""
FastAPI Backend - REST API for DocuScout Frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from .agent_handler import agent_handler

app = FastAPI(title="DocuScout API", version="1.0.0")

# CORS middleware to allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    agent: Optional[str] = None
    error: Optional[str] = None
    message: str

class IngestRequest(BaseModel):
    folder_path: Optional[str] = "DB"

class IngestResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    folder_path: str

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    error: Optional[str] = None
    query: str


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "ok",
        "service": "DocuScout API",
        "version": "1.0.0"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Send message to orchestrator agent
    """
    try:
        print(f"[API] Chat request received: {request.message[:50]}...")
        result = await agent_handler.chat(
            message=request.message,
            conversation_id=request.conversation_id
        )
        print(f"[API] Chat response: success={result.get('success', False)}, has_response={bool(result.get('response'))}")
        if not result.get('response'):
            print(f"[API] Warning: No response in result. Full result: {result}")
        return ChatResponse(**result)
    except Exception as e:
        print(f"[API] Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """
    Ingest documents from folder
    """
    try:
        folder_path = request.folder_path or "DB"
        print(f"[API] Starting ingestion from folder: {folder_path}")
        result = await agent_handler.ingest_documents(folder_path)
        print(f"[API] Ingestion completed: {result.get('success', False)}")
        return IngestResponse(**result)
    except Exception as e:
        print(f"[API] Ingestion error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query ingested documents
    """
    try:
        result = await agent_handler.query_documents(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents")
async def get_agents():
    """
    Get list of available agents
    """
    # Return array directly for easier frontend consumption
    return [
            {
                "name": "Orchestrator",
                "description": "Routes requests to appropriate subagents",
                "type": "main"
            },
            {
                "name": "Greeter",
                "description": "Greets users and explains DocuScout",
                "type": "subagent"
            },
            {
                "name": "FileReader",
                "description": "Reads and extracts text from documents",
                "type": "subagent"
            },
            {
                "name": "ClauseHunter",
                "description": "Finds specific clauses in documents",
                "type": "subagent"
            },
            {
                "name": "RiskAuditor",
                "description": "Analyzes documents for risk deviations",
                "type": "subagent"
            },
            {
                "name": "Critic",
                "description": "Validates risk findings to prevent false alarms",
                "type": "subagent"
            },
            {
                "name": "Researcher",
                "description": "Fetches web pages to learn compliance rules",
                "type": "subagent"
            },
            {
                "name": "Consultor",
                "description": "Answers questions about ingested documents",
                "type": "subagent"
            }
        ]


if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # Ensure we're in the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if os.getcwd() != project_root:
        os.chdir(project_root)
        sys.path.insert(0, project_root)
    
    print("🚀 Starting DocuScout Backend Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📚 API docs available at: http://localhost:8001/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Use import string format for reload to work properly
    uvicorn.run(
        "backend.api:app",  # Import string format
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload for now to avoid issues
        log_level="info",
        timeout_keep_alive=300  # 5 minutes for long-running tasks
    )

