"""
db_setup.py

Runs at app startup. Creates the tables, the read-only login, and the demo data
if they are missing. Safe to run every time. If anything fails, the app still
starts and the problem is written to the log.
"""
import logging
import os

import psycopg2
from psycopg2 import sql

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY, ticket_id TEXT UNIQUE, title TEXT,
    body TEXT, resolution TEXT, category TEXT
);
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY, tier TEXT, monthly_spend NUMERIC, rate_limit INT
);
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY, ticket_id TEXT, event_type TEXT NOT NULL, detail TEXT,
    ticket_body_snippet TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

DEMO_TICKETS = [
    ("T-1001", "Login fails after password reset", "User reset password but still gets 401 on login.",
     "Cleared cached session tokens; user re-logged in successfully.", "auth"),
    ("T-1002", "API rate limit hit unexpectedly", "Customer says they hit rate limit despite low usage.",
     "Found a misconfigured burst limit on their tier; adjusted config.", "billing"),
    ("T-1003", "Webhook not firing", "Webhook events stopped arriving after endpoint URL change.",
     "Endpoint URL had trailing slash mismatch; corrected URL.", "integration"),
]


def ensure_database() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.warning("DATABASE_URL not set; skipping database setup")
        return
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(SCHEMA)
                cur.execute(
                    "INSERT INTO accounts VALUES ('ACC-001','enterprise',4200.00,10000) "
                    "ON CONFLICT (account_id) DO NOTHING;"
                )
                for t in DEMO_TICKETS:
                    cur.execute(
                        "INSERT INTO tickets (ticket_id,title,body,resolution,category) "
                        "VALUES (%s,%s,%s,%s,%s) ON CONFLICT (ticket_id) DO NOTHING;", t
                    )

                # read-only login used by the account lookup; password is kept in sync with .env
                pw = os.getenv("READONLY_DB_PASSWORD")
                if pw:
                    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'triage_readonly';")
                    verb = "ALTER" if cur.fetchone() else "CREATE"
                    cur.execute(sql.SQL(verb + " ROLE triage_readonly WITH LOGIN PASSWORD {};")
                                .format(sql.Literal(pw)))
                    cur.execute("SELECT current_database();")
                    db = cur.fetchone()[0]
                    cur.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO triage_readonly;")
                                .format(sql.Identifier(db)))
                    cur.execute("GRANT USAGE ON SCHEMA public TO triage_readonly;")
                    cur.execute("GRANT SELECT ON accounts TO triage_readonly;")
        finally:
            conn.close()
        logger.info("Database ready")
    except Exception:
        logger.exception("Database setup failed; lookups may not work")


