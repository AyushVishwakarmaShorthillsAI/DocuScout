"""
Agent Handler - Wraps ADK agents via HTTP client
"""
import logging
from typing import Optional, Dict, Any

from .services.adk_client import get_adk_client

logger = logging.getLogger(__name__)


class AgentHandler:
    """Handles interactions with ADK agents via HTTP"""
    
    def __init__(self):
        # No direct agent instantiation - agents run on ADK API server
        pass
    
    async def ingest_documents(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest documents by routing through Orchestrator agent via ADK API server.
        Uses the global session_id (created on first request, reused for all subsequent requests).
        
        Args:
            session_id: Optional session ID (ignored - always uses global session)
            
        Returns:
            Dict with success status, message, and session_id (global session)
        """
        try:
            logger.info("[AgentHandler] Requesting document ingestion via Orchestrator agent")
            
            # Route through Orchestrator agent via ADK client
            adk_client = await get_adk_client()
            
            # Message to Orchestrator - it will route to FileReader agent
            message = "ingest the files present in DB folder"
            
            # ADK client will use/create global session (session_id parameter is ignored)
            result = await adk_client.chat(
                message=message,
                user_id="docuscout_user",
                session_id=None  # Always use global session
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Ingestion failed"),
                    "session_id": result.get("session_id")
                }
            
            return {
                "success": True,
                "message": result.get("response", "Documents ingested successfully"),
                "session_id": result.get("session_id")  # Return session_id for frontend to reuse
            }
        except Exception as e:
            logger.error(f"[AgentHandler] Error in ingest_documents: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message to the Orchestrator agent, instructing it to use Consultor subagent.
        Uses the global session_id (same session for all requests).
        
        Args:
            message: User's question
            session_id: Optional session ID (ignored - always uses global session)
            
        Returns:
            Dict with success status, response, and session_id (global session)
        """
        try:
            logger.info("[AgentHandler] Processing Q&A chat message")
            
            # Route through Orchestrator agent via ADK client
            # ADK client will use/create global session (session_id parameter is ignored)
            adk_client = await get_adk_client()
            
            logger.info("[AgentHandler] Using global session for Q&A")
            
            # Construct message that instructs Orchestrator to use Consultor subagent
            # The Orchestrator agent should route questions to Consultor based on its instructions
            # But we'll be explicit to ensure it uses Consultor
            formatted_message = f"""Answer this question about the ingested documents using the Consultor subagent:

{message}

Please use the Consultor agent to answer this question based on the content of the ingested documents."""
            
            # ADK client will use/create global session (session_id parameter is ignored)
            result = await adk_client.chat(
                message=formatted_message,
                user_id="docuscout_user",
                session_id=None  # Always use global session
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Chat failed"),
                    "response": result.get("response", "I encountered an error. Please try again."),
                    "session_id": session_id
                }
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "session_id": result.get("session_id", session_id)
            }
        except Exception as e:
            logger.error(f"[AgentHandler] Error in chat: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "session_id": session_id
            }


# Global instance
agent_handler = AgentHandler()

