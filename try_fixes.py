from agent.nodes.intent_routing import _keyword_fallback
from agent.nodes.safety_verification import safety_verification

print(_keyword_fallback("Webhook is down, urgent!"))
# {'category': 'integration', 'urgency': 'high'}

state = {
    "safety_flags": ["tool_error: ticket_lookup: OperationalError"],
    "tool_results": {
        "sandbox_runner": {"exit_code": -1},
        "account_context_db": {"error": "No account found"},
    },
}
print(safety_verification(state)["safety_flags"])
# ['tool_error: ticket_lookup: OperationalError',
#  'sandbox_execution_error', 'account_lookup_failed']