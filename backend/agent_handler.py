"""
Agent Handler - Wraps ADK agents via HTTP client
"""
import logging
from typing import Optional, Dict, Any, Callable

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
            message = "process and load the files from the DB folder"
            
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
            formatted_message = f"""Provide an answer to this question about the processed documents using the Consultor subagent:

{message}

Please use the Consultor agent to respond based on the document content."""
            
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
    
    async def predict_warnings(
        self,
        session_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Predict warnings by sequentially calling ClauseHunter, Researcher, and Critic agents.
        Uses the global session_id (same session for all requests).
        
        Args:
            session_id: Optional session ID (ignored - always uses global session)
            progress_callback: Optional callback function to report progress (message: str)
            
        Returns:
            Dict with success status, report content, and any errors
        """
        try:
            import time
            start_time = time.time()
            logger.info("=" * 80)
            logger.info("[AgentHandler] 🚀 Starting Predict Warnings workflow")
            logger.info("=" * 80)
            
            adk_client = await get_adk_client()
            
            # Step 1: Call ClauseHunter
            step1_start = time.time()
            logger.info("[AgentHandler] 📋 STEP 1/3: Starting ClauseHunter agent")
            logger.info("[AgentHandler] 📋 STEP 1/3: Message: 'extract and identify clauses from all the input files'")
            if progress_callback:
                import json
                progress_callback(json.dumps({
                    "step": 1,
                    "status": "in_progress",
                    "message": "Extracting clauses from documents..."
                }))
            
            clause_hunter_result = await adk_client.chat(
                message="extract and identify clauses from all the input files",
                user_id="docuscout_user",
                session_id=None  # Always use global session
            )
            
            step1_elapsed = time.time() - step1_start
            if not clause_hunter_result.get("success"):
                error_msg = clause_hunter_result.get("error", "ClauseHunter failed")
                logger.error(f"[AgentHandler] ❌ STEP 1/3 FAILED after {step1_elapsed:.2f}s: {error_msg}")
                return {
                    "success": False,
                    "error": f"Clause extraction failed: {error_msg}",
                    "step": "clause_hunter"
                }
            
            logger.info(f"[AgentHandler] ✅ STEP 1/3 COMPLETED in {step1_elapsed:.2f}s: ClauseHunter succeeded")
            logger.info(f"[AgentHandler] 📋 STEP 1/3: Response length: {len(clause_hunter_result.get('response', ''))} chars")
            if progress_callback:
                progress_callback(json.dumps({
                    "step": 1,
                    "status": "complete",
                    "message": "Clauses extracted successfully"
                }))
            
            # Step 2: Call Researcher
            step2_start = time.time()
            logger.info("[AgentHandler] 🔍 STEP 2/3: Starting Researcher agent")
            logger.info("[AgentHandler] 🔍 STEP 2/3: Message: 'Review and gather information about each legal term in dynamic_playbook.json'")
            if progress_callback:
                progress_callback(json.dumps({
                    "step": 2,
                    "status": "in_progress",
                    "message": "Researching legal amendments and updates..."
                }))
            
            researcher_result = await adk_client.chat(
                message="Review and gather information about each legal term in dynamic_playbook.json",
                user_id="docuscout_user",
                session_id=None  # Always use global session
            )
            
            step2_elapsed = time.time() - step2_start
            if not researcher_result.get("success"):
                error_msg = researcher_result.get("error", "Researcher failed")
                logger.error(f"[AgentHandler] ❌ STEP 2/3 FAILED after {step2_elapsed:.2f}s: {error_msg}")
                return {
                    "success": False,
                    "error": f"Legal research failed: {error_msg}",
                    "step": "researcher"
                }
            
            logger.info(f"[AgentHandler] ✅ STEP 2/3 COMPLETED in {step2_elapsed:.2f}s: Researcher succeeded")
            logger.info(f"[AgentHandler] 🔍 STEP 2/3: Response length: {len(researcher_result.get('response', ''))} chars")
            if progress_callback:
                progress_callback(json.dumps({
                    "step": 2,
                    "status": "complete",
                    "message": "Legal research completed"
                }))
            
            # Step 3: Call RiskAuditor (formerly Critic)
            step3_start = time.time()
            logger.info("[AgentHandler] ⚖️  STEP 3/3: Starting RiskAuditor agent")
            logger.info("[AgentHandler] ⚖️  STEP 3/3: Message: 'analyze compliance status across different files'")
            if progress_callback:
                progress_callback(json.dumps({
                    "step": 3,
                    "status": "in_progress",
                    "message": "Analyzing risks and generating report..."
                }))
            
            risk_auditor_result = await adk_client.chat(
                message="analyze compliance status across different files",
                user_id="docuscout_user",
                session_id=None  # Always use global session
            )
            
            step3_elapsed = time.time() - step3_start
            if not risk_auditor_result.get("success"):
                error_msg = risk_auditor_result.get("error", "RiskAuditor failed")
                logger.error(f"[AgentHandler] ❌ STEP 3/3 FAILED after {step3_elapsed:.2f}s: {error_msg}")
                return {
                    "success": False,
                    "error": f"Risk analysis failed: {error_msg}",
                    "step": "risk_auditor"
                }
            
            logger.info(f"[AgentHandler] ✅ STEP 3/3 COMPLETED in {step3_elapsed:.2f}s: RiskAuditor succeeded")
            logger.info(f"[AgentHandler] ⚖️  STEP 3/3: Response length: {len(risk_auditor_result.get('response', ''))} chars")
            if progress_callback:
                progress_callback(json.dumps({
                    "step": 3,
                    "status": "complete",
                    "message": "Risk analysis completed"
                }))
            
            # Read the final report from risk_audit_report.md
            logger.info("[AgentHandler] 📄 Reading final report from risk_audit_report.md")
            try:
                from pathlib import Path
                report_path = Path(__file__).parent.parent / "risk_audit_report.md"
                if report_path.exists():
                    report_content = report_path.read_text(encoding="utf-8")
                    logger.info(f"[AgentHandler] ✅ Successfully read risk_audit_report.md ({len(report_content)} chars)")
                else:
                    logger.warning("[AgentHandler] ⚠️  risk_audit_report.md not found, using agent response")
                    report_content = risk_auditor_result.get("response", "Report generated successfully.")
            except Exception as e:
                logger.warning(f"[AgentHandler] ⚠️  Error reading report file: {str(e)}, using agent response")
                report_content = risk_auditor_result.get("response", "Report generated successfully.")
            
            total_elapsed = time.time() - start_time
            logger.info("=" * 80)
            logger.info(f"[AgentHandler] 🎉 Predict Warnings workflow COMPLETED successfully in {total_elapsed:.2f}s")
            logger.info(f"[AgentHandler] 📊 Timing breakdown:")
            logger.info(f"[AgentHandler]    - Step 1 (ClauseHunter): {step1_elapsed:.2f}s")
            logger.info(f"[AgentHandler]    - Step 2 (Researcher): {step2_elapsed:.2f}s")
            logger.info(f"[AgentHandler]    - Step 3 (RiskAuditor): {step3_elapsed:.2f}s")
            logger.info(f"[AgentHandler]    - Total: {total_elapsed:.2f}s")
            logger.info("=" * 80)
            
            if progress_callback:
                progress_callback("Analysis complete!")
            
            return {
                "success": True,
                "report": report_content,
                "session_id": risk_auditor_result.get("session_id")
            }
            
        except Exception as e:
            logger.error(f"[AgentHandler] Error in predict_warnings: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "step": "unknown"
            }


# Global instance
agent_handler = AgentHandler()

