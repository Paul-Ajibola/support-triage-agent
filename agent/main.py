# agent/main.py

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

class TicketRequest(BaseModel):
    ticket_id: str
    body: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ticket")
def handle_ticket(ticket: TicketRequest):
    result = graph.invoke(
        {
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
            "flag_reason": None
        },
        config = {"configurable": {"thread_id": ticket.ticket_id}},
    )

    return {
        "ticket_id": ticket.ticket_id,
        "status": "flagged" if result.get("is_flagged") else "processed",
        "category": result.get("category"),
        "urgency": result.get("urgency"),
        "response": result.get("draft_response"),
        "safety_flags": result.get("safety_flags", []),
    }


