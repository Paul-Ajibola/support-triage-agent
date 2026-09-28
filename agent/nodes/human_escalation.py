"""
human_escalation.py

Node: terminal step for tickets flagged by the injection guardrail.
For now, produces a safe placeholder response and stops the pipeline
here rather than continuing to automated classisification or tool use. 
"""

# import state for the agent
from agent.state import AgentState


def human_escalation(state: AgentState) -> AgentState:
    state["draft_response"] = (
        "This ticket has been flagged for manual review by the security team "
        " and will not be processed automatically"
    )
    state["category"] = "flagged"
    state["urgency"] = "critical"
    return state
