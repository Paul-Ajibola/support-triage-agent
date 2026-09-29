"""
Writes security events (guardrail catches, tool validation failures)
to a persistent Postgres table, so attempted manipulation leaves a 
real, reviewable trail rather than only appearning in a single request's transient
state.
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging


load_dotenv(".env")

logger = logging.getLogger(__name__)


def log_security_event(ticket_id: str, event_type: str, detail: str, ticket_body: str = "") -> None:
    snippet = ticket_body[:200] if ticket_body else None
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
        try:
             with conn, conn.cursor() as cur:      
                cur.execute("""
                    INSERT INTO security_audit_log (ticket_id, event_type, detail, ticket_body_snippet)
                    VALUES (%s, %s, %s, %s);
                """, (ticket_id, event_type, detail, snippet))
        finally:
            conn.close()
    except Exception:
        logger.exception(
            "Could not write security audit event (ticket=%s, type=%s)", ticket_id, event_type
        )

