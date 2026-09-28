"""
injection_guardrail.py

Screens the raw ticket body for prompt-injection attempts before any other 
node processes it. Flagged tickets are marked in state, logged to the audit trail,
and routed to human escalation
"""


from agent.state import AgentState
from agent.security.guardrail import scan_for_injection
from agent.security.audit_log import log_security_event



def injection_guardrail(state: AgentState) -> AgentState:
    result = scan_for_injection(state["body"])
    state["is_flagged"] = result["is_injection"]
    state["flag_reason"] = result["reason"] if result["is_injection"] else None

    if result["is_injection"]:
        log_security_event(
            ticket_id=state.get("ticket_id", "unknown"),
            event_type="injection_flagged",
            detail=result["reason"],
            ticket_body=state["body"]
        )
    return state


