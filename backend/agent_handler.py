"""
Agent Handler - Wraps ADK agents for programmatic access
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import Agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from Agent.agent import root_agent
from Agent.Subagents.FileReader.tools import ingest_documents
from Agent.Subagents.Consultor.tools import query_docs
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
import asyncio
from typing import Optional, Dict, Any


class AgentHandler:
    """Handles interactions with ADK agents"""
    
    def __init__(self):
        self.root_agent = root_agent
        # Create a session service and runner for proper agent execution
        self.session_service = InMemorySessionService()
        self.runner = Runner(agent=root_agent, session_service=self.session_service, app_name="DocuScout")
    
    async def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to the orchestrator agent and get response
        
        Args:
            message: User message
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dict with response, agent_used, and metadata
        """
        try:
            print(f"[AgentHandler] Processing chat message: {message[:50]}...")
            
            # Use Runner to execute the agent properly
            # Create Content object from message string
            content = genai_types.Content(parts=[genai_types.Part(text=message)])
            
            response_text = ""
            async for event in self.runner.run_async(
                user_id="docuscout_user",
                session_id=conversation_id or "default",
                new_message=content
            ):
                # Collect text from events - handle different event types safely
                try:
                    if hasattr(event, 'text') and event.text:
                        response_text += str(event.text)
                    elif hasattr(event, 'content') and event.content:
                        response_text += str(event.content)
                    elif hasattr(event, 'message') and event.message:
                        response_text += str(event.message)
                    elif hasattr(event, 'output') and event.output:
                        response_text += str(event.output)
                    elif isinstance(event, str):
                        response_text += event
                    else:
                        # Try to get string representation safely
                        try:
                            response_text += str(event)
                        except:
                            # Skip events that can't be converted
                            pass
                except Exception as event_error:
                    print(f"[AgentHandler] Error processing event: {event_error}")
                    # Continue processing other events
                    pass
            
            print(f"[AgentHandler] Agent response length: {len(response_text)}")
            
            # Handle None or empty response
            if not response_text or not response_text.strip():
                response_text = "I apologize, but I didn't receive a response. Please try again."
            else:
                response_text = response_text.strip()
            
            return {
                "success": True,
                "response": response_text,
                "agent": "Orchestrator",
                "message": message
            }
        except Exception as e:
            print(f"[AgentHandler] Error in chat: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "message": message
            }
    
    async def ingest_documents(self, folder_path: str = "DB") -> Dict[str, Any]:
        """
        Ingest documents from folder (async wrapper for sync function)
        
        Args:
            folder_path: Path to folder containing documents
            
        Returns:
            Dict with success status and message
        """
        try:
            # Run the synchronous ingest_documents function in a thread pool
            result = await asyncio.to_thread(ingest_documents, folder_path)
            return {
                "success": True,
                "message": result,
                "folder_path": folder_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "folder_path": folder_path
            }
    
    async def query_documents(self, query: str) -> Dict[str, Any]:
        """
        Query ingested documents (async wrapper for sync function)
        
        Args:
            query: Question to ask about documents
            
        Returns:
            Dict with answer and metadata
        """
        try:
            # Run the synchronous query_docs function in a thread pool
            result = await asyncio.to_thread(query_docs, query)
            return {
                "success": True,
                "answer": result,
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }


# Global instance
agent_handler = AgentHandler()

