
# agent/main.py
import hmac
import psycopg2
import os
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv(".env")

from agent.graph import graph                                   # noqa: E402
from agent.checkpointing import close_checkpointer              # noqa: E402
from agent.classifier import warm_up                            # noqa: E402

from agent.db_setup import ensure_database


def _env() -> str:
    return os.getenv("APP_ENV", "development").lower()


def demo_mode() -> bool:
    """DEMO_MODE=true: public demo. No API key needed, but requests are rate limited."""
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def check_config() -> None:
    """Fail at startup, not on the first request, if production is misconfigured."""
    if _env() == "production":
        if not demo_mode() and not os.getenv("API_KEY"):
            raise RuntimeError("API_KEY must be set when APP_ENV=production (or set DEMO_MODE=true)")
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY must be set: the injection guardrail needs it, "
                               "and without it every ticket is escalated")


check_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database()
    warm_up()
    yield
    close_checkpointer()


app = FastAPI(title="Support Triage Agent", lifespan=lifespan)



# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# The UI is served from the same origin, so CORS is off unless origins are listed.
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if _origins:
    app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["*"])


def require_api_key(x_api_key: str = Header(default="")):
    if demo_mode() or _env() == "development":
        return
    expected = os.getenv("API_KEY", "")
    if not expected or not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")



# ---- demo-mode rate limiting (in-memory; fine for a single-process demo) ----
_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)
_daily = {"day": "", "n": 0}



def rate_limit(request: Request):
    if not demo_mode():
        return
    per_min = int(os.getenv("RATE_LIMIT_PER_MIN", "8"))
    daily_cap = int(os.getenv("DAILY_CAP", "300"))   # global cap protects the Groq quota
    # X-Forwarded-For is only trustworthy behind your own proxy; the daily cap holds regardless.
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
          or (request.client.host if request.client else "unknown"))
    now, today = time.time(), time.strftime("%Y-%m-%d")
    with _lock:
        if _daily["day"] != today:
            _daily.update(day=today, n=0)
        if _daily["n"] >= daily_cap:
            raise HTTPException(429, "The demo hit its daily limit. Please try again tomorrow.")
        q = _hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= per_min:
            raise HTTPException(429, f"Rate limit: max {per_min} tickets per minute. Please wait a moment.")
        q.append(now)
        _daily["n"] += 1



class TicketRequest(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=10000)



@app.get("/health")
def health():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), connect_timeout=3)
        conn.close()
        database = "ok"
    except Exception:
        database = "down"
    memory = type(graph.checkpointer).__name__ in ("MemorySaver", "InMemorySaver")
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "conversation_storage": "in-memory (Redis not connected)" if memory else "redis",
    }



@app.get("/config")
def config():
    return {"demo_mode": demo_mode(), "requires_api_key": not demo_mode() and _env() != "development"}


@app.post("/ticket", dependencies=[Depends(require_api_key), Depends(rate_limit)])
def _public_tools(tool_results: dict) -> dict:
    """Trimmed, UI-safe view of tool results (no raw account or spend data)."""
    out = {"tool_status": {}, "similar_tickets": []}
    for name, value in (tool_results or {}).items():
        failed = isinstance(value, dict) and "error" in value
        out["tool_status"][name] = "error" if failed else "ok"
    lookup = (tool_results or {}).get("ticket_lookup")
    if isinstance(lookup, list):
        out["similar_tickets"] = [
            {"ticket_id": t.get("ticket_id"), "title": t.get("title"), "category": t.get("category")}
            for t in lookup if isinstance(t, dict)
        ]
    return out


def handle_ticket(ticket: TicketRequest):
    config = {"configurable": {"thread_id": ticket.ticket_id}}

    saved = graph.get_state(config)
    if saved and saved.values:
        payload = {"body": ticket.body}
    else:
        payload = {
            "ticket_id": ticket.ticket_id, "body": ticket.body,
            "category": None, "urgency": None, "tools_to_call": [], "tool_results": {},
            "safety_flags": [], "draft_response": None, "turn_count": 0,
            "conversation_history": [], "is_flagged": False, "flag_reason": None,
            "guardrail_unavailable": False, "draft_source": None,
        }

    result = graph.invoke(payload, config=config)

    if result.get("guardrail_unavailable"):
        status = "guardrail_unavailable"
    elif result.get("is_flagged"):
        status = "flagged"
    else:
        status = "processed"

    return {
        "ticket_id": ticket.ticket_id,
        "status": status,
        "category": result.get("category"),
        "urgency": result.get("urgency"),
        "classifier": None if result.get("is_flagged") else result.get("classifier"),
        "response": result.get("draft_response"),
        "draft_source": result.get("draft_source"),
        "flag_reason": result.get("flag_reason"),
        "safety_flags": result.get("safety_flags", []),
        "tool_results": {} if result.get("is_flagged") else _public_tools(result.get("tool_results", {})),
        "turn_count": result.get("turn_count", 0),
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")


