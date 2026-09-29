"""
tool_execution.py

Node: calls each tool listed in tools_to_call (ticket_lookup,
sandbox_runner, account_context_db) and collects their results into
tool_results for use by later nodes.
"""

# import libraries

import logging

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


logger = logging.getLogger(__name__)


# new tool_execution node with tool_validation
def tool_execution(state: AgentState) -> AgentState:
    results = {}
    flags = []                       # fresh every turn, so flags don't pile up across turns
    ticket_id = state.get("ticket_id", "unknown")
    body = state.get("body", "")
    tools = state.get("tools_to_call", [])

    def run(tool_name, validate, call, arg):
        """Validate, then call one tool. Never raises."""
        try:
            validate(arg)
            results[tool_name] = call(arg)
        except ToolValidationError as e:
            log_security_event(
                ticket_id=ticket_id,
                event_type="tool_validation_failed",
                detail=f"{tool_name}: {e}",
                ticket_body=body,
            )
            flags.append(f"tool_validation_failed: {e}")
            results[tool_name] = {"error": str(e)}
        except Exception as e:       # DB down, docker missing, etc.
            logger.exception("Tool %s failed", tool_name)
            flags.append(f"tool_error: {tool_name}: {type(e).__name__}")
            results[tool_name] = {"error": f"{tool_name} failed: {type(e).__name__}"}

    if "ticket_lookup" in tools:
        run("ticket_lookup", validate_ticket_lookup, ticket_lookup, body)

    if "sandbox_runner" in tools:
        # stub until real code extraction from tickets exists
        run("sandbox_runner", validate_sandbox_runner, sandbox_runner, "print('reproduction stub')")

    if "account_context_db" in tools:
        # placeholder account_id until real ticket -> account mapping exists
        run("account_context_db", validate_account_context_db, account_context_db, "ACC-001")

    state["tool_results"] = results
    state["safety_flags"] = flags
    return state

