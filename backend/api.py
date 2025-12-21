"""
FastAPI Backend - REST API for DocuScout Frontend
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from pathlib import Path

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

# Ensure DB folder exists
DB_FOLDER = Path("DB")
DB_FOLDER.mkdir(exist_ok=True)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Optional - ignored, always uses global session

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None

class IngestResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    files_uploaded: int = 0


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "ok",
        "service": "DocuScout API",
        "version": "1.0.0"
    }


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_documents(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Query(None)  # Ignored - always uses global session
):
    """
    Upload PDF files and ingest them via Orchestrator agent.
    
    This endpoint:
    1. Receives PDF files from frontend
    2. Saves them to DB folder
    3. Calls Orchestrator agent via ADK client to ingest files
    4. Returns global session_id (same session used for all requests)
    
    IMPORTANT: Uses a global session_id that is shared across all requests.
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Save files to DB folder
        saved_files = []
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                continue  # Skip non-PDF files
            
            # Save file to DB folder
            file_path = DB_FOLDER / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)
            print(f"[API] Saved file: {file.filename}")
        
        if not saved_files:
            raise HTTPException(status_code=400, detail="No valid PDF files provided")
        
        print(f"[API] Saved {len(saved_files)} files to DB folder")
        print(f"[API] Starting ingestion via Orchestrator agent...")
        print(f"[API] Using global session_id (shared across all requests)")
        
        # Call agent handler to ingest via ADK client
        # ADK client will create/use global session (session_id parameter is ignored)
        result = await agent_handler.ingest_documents(session_id=None)
        
        print(f"[API] Ingestion completed: success={result.get('success', False)}")
        
        return IngestResponse(
            success=result.get("success", False),
            message=result.get("message", "Ingestion completed"),
            error=result.get("error"),
            session_id=result.get("session_id"),
            files_uploaded=len(saved_files)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Ingestion error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Send question to Orchestrator agent (which routes to Consultor subagent).
    
    This endpoint:
    1. Receives user's question
    2. Calls Orchestrator agent via ADK client using the GLOBAL session_id
    3. Orchestrator routes to Consultor subagent to answer the question
    4. Returns the answer
    
    IMPORTANT: Uses a global session_id that is shared across all requests (ingestion, Q&A, etc.)
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        print(f"[API] Chat request received: {request.message[:50]}...")
        print(f"[API] Using global session_id (shared across all requests)")
        
        # session_id parameter is optional and ignored - always uses global session
        result = await agent_handler.chat(
            message=request.message,
            session_id=None  # Always use global session
        )
        
        print(f"[API] Chat response: success={result.get('success', False)}")
        print(f"[API] Global session ID used: {result.get('session_id')}")
        
        return ChatResponse(
            success=result.get("success", False),
            response=result.get("response"),
            error=result.get("error"),
            session_id=result.get("session_id")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Use import string format for reload to work properly
    uvicorn.run(
        "backend.api:app",  # Import string format
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for now to avoid issues
        log_level="info",
        timeout_keep_alive=300  # 5 minutes for long-running tasks
    )

