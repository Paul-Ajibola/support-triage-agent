"""
tool_execution.py

Node: calls each tool listed in tools_to_call (ticket_lookup,
sandbox_runner, account_context_db) and collects their results into
tool_results for use by later nodes.
"""

# import libraries
from agent.state import AgentState
from tools.ticket_lookup import ticket_lookup
from tools.sandbox_runner import sandbox_runner
from tools.account_context_db import account_context_db
from agent.tool_validation import (
    validate_ticket_lookup,
    validate_account_context_db,
    validate_sandbox_runner,
    ToolValidationError,
)
from agent.security.audit_log import log_security_event


# # INITIAL TOOL_EXECUTION NODE
# def tool_execution(state: AgentState) -> AgentState:
#     results = {}

#     if "ticket_lookup" in state["tools_to_call"]:
#         results["ticket_lookup"] = ticket_lookup(state["body"])

#     if "sandbox_runner" in state["tools_to_call"]:
#         results["sandbox_runner"] = sandbox_runner("print('reproduction stub')")

#     if "account_context_db" in state["tools_to_call"]:
#         # placeholder account_id until real ticket -> account mapping exists
#         results["account_context_db"] = account_context_db("ACC-001")

    
#     state["tool_results"] = results
#     return state


# new tool_execution node with tool_validation

def tool_execution(state: AgentState) -> AgentState:
    results = {}
    validation_errors = []

    if "ticket_lookup" in state["tools_to_call"]:
        try:
            validate_ticket_lookup(state["body"])
            results["ticket_lookup"] = ticket_lookup(state["body"])
        except ToolValidationError as e:
            log_security_event(
                ticket_id=state.get("tocket_id", "unknown"), 
                event_type="tool_validation_failed",
                detail=f"ticket_lookup: {e}",
                ticket_body=state.get("body", ""),
                )
            validation_errors.append(str(e))
            results["ticket_lookup"] = {"error": str(e)}

    if "sandbox_runner" in state["tools_to_call"]:
        sandbox_code = "print('reproduction stub')"
        try:
            validate_sandbox_runner(sandbox_code)
            results["sandbox_runner"] = sandbox_runner(sandbox_code)
        except ToolValidationError as e:
            log_security_event("tool_validation_failed", details={"tool": "sandbox_runner", "error": str(e)})
            validation_errors.append(str(e))
            results["sandbox_runner"] = {"error": str(e)}

    if "account_context_db" in state["tools_to_call"]:
        account_id = "ACC-001"
        try:
            validate_account_context_db(account_id)
            results["account_context_db"] = account_context_db(account_id)
        except ToolValidationError as e:
            log_security_event(
                ticket_id=state.get("ticket_id", "unknown"), 
                event_type="tool_validation_failed",
                detail=f"account_context_db: {e}",
                ticket_body=state.get("body", ""),
                )
            validation_errors.append(str(e))
            results["account_context_db"] = {"error": str(e)}

    state["tool_results"] = results
    if validation_errors:
        state["safety_flags"] = state.get("safety_flags", []) + [
            f"tool_validation_failed: {err}" for err in validation_errors
        ]

    return state


