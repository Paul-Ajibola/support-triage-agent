"""
intent_routing.py

Node: classifies an incoming ticket by category (auth, billing,
integration, general) and urgency (high, normal) using simple keyword
matching. First step in the graph — determines routing for later nodes.
"""

# import libraries
from agent.state import AgentState
from agent.classifier import classify_ticket_finetuned
import json
import logging


logging = logging.getLogger(__name__)


def _keyword_fallback(body: str) -> dict:
    "Determines what is the intent of the ticket and classifies its urgency"
    body = state["body"].lower()

    if "login" in body or "password" in body or "auth" in body:
        category = "auth"
    elif "rate limit" in body or "billing" in body or "charge" in body:
        category = "billing"
    elif "webhook" in body or "intention" in body or "api" in body:
        category = "integration"
    else:
        category = "general"
    
    urgency = "high" if any(
        w in body for w in ["down", "broken", "urgent", "critical"]
        ) else "normal"


    # add the decision back into the state
    return {"category": category, "urgency": urgency}



def intent_routing(state: AgentState) -> AgentState:
    "Determines the intent of the ticket and classifies its urgency"
    try:
        result = classify_ticket_finetuned(state["body"])
    except Exception:
        logger.warning("classifier failed, using keyword fallback", exc_info=True)
        result = _keyword_fallback(state["body"])
        

    state["category"] = result["category"]
    state["urgency"] = result["urgency"]
    return state



