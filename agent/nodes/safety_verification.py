"""
safety_verification.py

Node: sanity-checks tool_results for failures (sandbox errors, failed
account lookups) and records them as safety_flags. Placeholder for
real adversarial/injection defense, added in Phase 7.
"""

# import libraries
from agent.state import AgentState


def safety_verification(state: AgentState) -> AgentState:
    flags = list(state.get("safety_flags", []))

    tool_results = state.get("tool_results", {})

    sandbox_result = tool_results.get("sandbox_runner")
    if sandbox_result and sandbox_result.get("exit_code", 0) != 0:
        flags.append("sandbox_execution_error")
    
    account_result = tool_results.get("account_context_db")
    if account_result and "error" in account_result:
        flags.append("account_lookup_failed")

    state["safety_flags"] = list(dict.fromkeys(flags))
    return state

