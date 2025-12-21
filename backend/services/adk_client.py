"""
ADK Client Service

Handles communication with the Google ADK API Server for agent execution.
The Agent (Orchestrator) agent handles all routing to subagents.

Author: DocuScout Team
"""

import os
import logging
import time
import uuid
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

# ADK API Server Configuration
ADK_API_URL = os.getenv("ADK_API_URL", "http://localhost:8001")
ADK_REQUEST_TIMEOUT = None  # No timeout - wait indefinitely for agent response

# Global session storage - ONE session for all requests
_global_session_id: Optional[str] = None


class ADKClient:
    """Client for communicating with Google ADK API Server."""
    
    def __init__(self, api_url: str = ADK_API_URL):
        self.api_url = api_url
        # Set timeout=None to wait indefinitely for long-running agent tasks
        self.client = httpx.AsyncClient(timeout=ADK_REQUEST_TIMEOUT)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get_or_create_global_session(self, agent_name: str, user_id: str) -> str:
        """
        Get or create a GLOBAL session for all requests.
        Only ONE session is created and reused for all agent interactions.
        
        Args:
            agent_name: Name of the agent (e.g., "Agent")
            user_id: User identifier
            
        Returns:
            Global session ID string
        """
        global _global_session_id
        
        # If global session already exists, reuse it
        if _global_session_id:
            logger.debug(f"♻️  Reusing global session: {_global_session_id[:20]}...")
            return _global_session_id
        
        # Create new global session
        session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        try:
            session_url = f"{self.api_url}/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
            logger.info(f"🔄 Creating new GLOBAL session for {agent_name}: {session_id}")
            
            response = await self.client.post(session_url, json={})
            response.raise_for_status()
            
            # Store as global session
            _global_session_id = session_id
            logger.info(f"✅ Global session created and stored: {session_id}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create global session: {e}")
            raise Exception(f"Failed to create ADK session: {str(e)}")
    
    async def chat(
        self,
        message: str,
        user_id: str = "docuscout_user",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message to the Agent (Orchestrator) agent.
        
        Args:
            message: User message
            user_id: User identifier
            session_id: Optional session ID (if None, will get or create)
            
        Returns:
            Dict containing:
                - success: bool
                - response: str (agent response text)
                - session_id: str (session ID used)
                - error: Optional[str]
        """
        agent_name = "Agent"
        
        try:
            # Always use the global session (create if doesn't exist)
            # If session_id is provided, it should be the global one, but we'll use global anyway
            global_session_id = await self.get_or_create_global_session(agent_name, user_id)
            
            # Use global session (ignore provided session_id to ensure consistency)
            session_id = global_session_id
            logger.info(f"♻️  Using global session_id: {session_id[:20]}...")
            
            # Call ADK agent via HTTP
            run_url = f"{self.api_url}/run"
            logger.info(f"🚀 Calling Agent (Orchestrator) at {run_url} (session: {session_id[:20]}...)")
            logger.info(f"📝 Message: {message[:100]}...")
            
            request_data = {
                "app_name": agent_name,
                "user_id": user_id,
                "session_id": session_id,
                "new_message": {
                    "role": "user",
                    "parts": [
                        {
                            "text": message
                        }
                    ]
                },
                "streaming": False
            }
            
            start_time = time.time()
            logger.info(f"📤 Sending HTTP POST request at {start_time:.3f}")
            response = await self.client.post(run_url, json=request_data)
            response.raise_for_status()
            elapsed_time = time.time() - start_time
            
            logger.info(f"⏱️  Agent response received in {elapsed_time:.2f}s")
            
            # Parse response
            events = response.json()
            
            if not events or len(events) == 0:
                raise Exception("Empty response from agent")
            
            # Extract text response from events
            response_text = self._extract_text_response(events)
            
            if not response_text:
                logger.warning("⚠️  No text response found in agent events")
                raise Exception("Agent did not return text response")
            
            logger.info(f"✅ Agent returned response ({len(response_text)} chars)")
            
            return {
                "success": True,
                "response": response_text,
                "session_id": session_id
            }
        
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "session_id": session_id if session_id else None
            }
    
    def _extract_text_response(self, events: list) -> str:
        """
        Extract text response from ADK events.
        
        Args:
            events: List of event dictionaries from ADK API
            
        Returns:
            Concatenated text response
        """
        response_text = ""
        
        for event in events:
            content = event.get("content", {})
            parts = content.get("parts", [])
            
            for part in parts:
                if "text" in part:
                    response_text += part["text"]
        
        return response_text.strip()


# Global client instance
_adk_client: Optional[ADKClient] = None


async def get_adk_client() -> ADKClient:
    """Get or create the global ADK client instance."""
    global _adk_client
    if _adk_client is None:
        _adk_client = ADKClient()
    return _adk_client


async def close_adk_client():
    """Close the global ADK client instance."""
    global _adk_client
    if _adk_client is not None:
        await _adk_client.close()
        _adk_client = None

