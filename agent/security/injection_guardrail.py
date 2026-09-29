"""
injection_guardrail.py

Screens the raw ticket body for prompt-injection attempts before any other node
runs. Flagged tickets are logged and routed to human escalation. If the guardrail
model itself is down we still fail closed, but record it as "unavailable" so the
UI doesn't present a harmless ticket as an attack.
"""
from agent.state import AgentState
from agent.security.guardrail import scan_for_injection
from agent.security.audit_log import log_security_event


def injection_guardrail(state: AgentState) -> AgentState:
    result = scan_for_injection(state["body"])
    unavailable = bool(result.get("unavailable"))
    state["is_flagged"] = result["is_injection"]
    state["guardrail_unavailable"] = unavailable
    state["flag_reason"] = result["reason"] if result["is_injection"] else None

    if result["is_injection"]:
        log_security_event(
            ticket_id=state.get("ticket_id", "unknown"),
            event_type="guardrail_unavailable" if unavailable else "injection_flagged",
            detail=result["reason"],
            ticket_body=state["body"],
        )
    return state