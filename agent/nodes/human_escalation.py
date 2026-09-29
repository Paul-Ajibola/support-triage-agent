"""
human_escalation.py

Terminal step for tickets the guardrail did not clear: either a detected
injection attempt, or the guardrail service being unavailable (fail closed).
"""
from agent.state import AgentState


def human_escalation(state: AgentState) -> AgentState:
    if state.get("guardrail_unavailable"):
        state["draft_response"] = (
            "Our security screening service is temporarily unavailable, so this ticket was "
            "queued for manual review instead of being processed automatically. "
            "Please try again in a moment."
        )
        state["category"] = "pending_review"
        state["urgency"] = "normal"
    else:
        state["draft_response"] = (
            "This ticket has been flagged for manual review by the security team "
            "and will not be processed automatically."
        )
        state["category"] = "flagged"
        state["urgency"] = "critical"

    state["draft_source"] = "escalation"
    history = list(state.get("conversation_history", []))
    history.append(state["draft_response"])
    state["conversation_history"] = history
    state["turn_count"] = state.get("turn_count", 0) + 1
    return state