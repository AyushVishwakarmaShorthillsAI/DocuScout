from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

import os
import litellm

# Import subagents
from .Subagents.Greeter.agent import root_agent as greeter_agent
from .Subagents.FileReader.agent import root_agent as file_reader_agent
from .Subagents.ClauseHunter.agent import root_agent as clause_hunter_agent
from .Subagents.RiskAuditor.agent import root_agent as risk_auditor_agent
from .Subagents.Critic.agent import root_agent as critic_agent
from .Subagents.Researcher.agent import root_agent as researcher_agent
from .Subagents.Consultor.agent import root_agent as consultor_agent

load_dotenv()

litellm.use_litellm_proxy = True

lite_llm_model = LiteLlm(
    model=os.getenv("GEMINI_MODEL"),
    api_base=os.getenv("LITELLM_PROXY_API_BASE"),
    api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
)


root_agent = LlmAgent(
    name="Orchestrator",
    model=lite_llm_model,
    tools=[],
    sub_agents=[
        greeter_agent,
        file_reader_agent,
        clause_hunter_agent,
        risk_auditor_agent,
        critic_agent,
        researcher_agent,
        consultor_agent
    ],
    description="You route user requests to the appropriate subagents. You have agents for greeting, reading files, extracting clauses, analyzing compliance, reviewing contracts, researching legal updates, and consulting on document content.",
    instruction="""You are the Orchestrator. Route user requests to the appropriate subagent based on their needs.

**Routing Guide:**

1. **Greeter** - Use for: greetings, introductions, general help
   - Commands: "hello", "hi", "help", "what can you do"

2. **FileReader** - Use for: loading/processing documents from DB folder
   - Commands: "process files", "load files", "ingest files", "read documents from DB"

3. **ClauseHunter** - Use for: extracting legal clauses and entities from documents
   - Commands: "extract clauses", "identify clauses", "find legal entities", "analyze contract structure"

4. **Researcher** - Use for: researching legal updates and amendments
   - Commands: "research legal terms", "review legal updates", "gather information about laws", "check for amendments"

5. **RiskAuditor** - Use for: analyzing compliance status and generating audit reports
   - Commands: "analyze compliance", "check compliance status", "generate audit report", "review contract compliance"

6. **Critic** - Use for: reviewing and critiquing contract quality
   - Commands: "review contract", "critique contract", "analyze contract quality"

7. **Consultor** - Use for: answering questions about processed document content
   - Commands: "answer question about documents", "what does the contract say about...", "explain clause", "provide information from documents"

**Important:**
- Use Consultor for ALL questions about the content of processed documents
- Route based on the user's intent, not exact wording
- Only route to ONE subagent at a time
"""
)

