# agent/main.py
import hmac
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from agent.graph import graph
from agent.checkpointing import close_checkpointer

load_dotenv(".env")


def check_config() -> None:
    """Fail at startup, not on the first request, if production is misconfigured."""
    if os.getenv("APP_ENV", "development").lower() == "production" and not os.getenv("API_KEY"):
        raise RuntimeError("API_KEY must be set when APP_ENV=production")


check_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_checkpointer()          # runs on shutdown


app = FastAPI(title="Support Triage Agent", lifespan=lifespan)


def require_api_key(x_api_key: str = Header(default="")):
    """If API_KEY is set, callers must send it in the X-API-Key header.
    Only unset in local dev (check_config blocks that in production)."""
    expected = os.getenv("API_KEY", "")
    if expected and not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class TicketRequest(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=10000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ticket", dependencies=[Depends(require_api_key)])
def handle_ticket(ticket: TicketRequest):
    config = {"configurable": {"thread_id": ticket.ticket_id}}

    saved = graph.get_state(config)
    if saved and saved.values:
        payload = {"body": ticket.body}
    else:
        payload = {
            "ticket_id": ticket.ticket_id,
            "body": ticket.body,
            "category": None,
            "urgency": None,
            "tools_to_call": [],
            "tool_results": {},
            "safety_flags": [],
            "draft_response": None,
            "turn_count": 0,
            "conversation_history": [],
            "is_flagged": False,
            "flag_reason": None,
        }

    result = graph.invoke(payload, config=config)

    return {
        "ticket_id": ticket.ticket_id,
        "status": "flagged" if result.get("is_flagged") else "processed",
        "category": result.get("category"),
        "urgency": result.get("urgency"),
        "classifier": result.get("classifier")
        "response": result.get("draft_response"),
        "safety_flags": result.get("safety_flags", []),
        "turn_count": result.get("turn_count", 0),
    }