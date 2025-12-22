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
    model="hackathon-gemini-2.5-flash",
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
    description="You route user requests to the appropriate subagents. You have agents for greeting, reading files, hunting clauses, auditing risks, criticizing contracts, researching, and consulting on document content.",
    instruction="Route user requests to the appropriate subagent based on their needs. Use the Consultor agent for answering questions about the content of ingested documents."
)

