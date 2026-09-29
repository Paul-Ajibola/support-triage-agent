"""
account_context_db.py

Tool: read-only lookup of account tier, monthly spend, and rate limit
for a given account_id. Used by the agent to pull customer context
when triaging a ticket.

Requires: Postgres running, DATABASE_URL set in .env.local, accounts
table seeded (see seed_accounts.py).
"""
import psycopg2
import os

from dotenv import load_dotenv

load_dotenv(".env")

def account_context_db(account_id: str) -> dict:
    """Read-only lookup of account tier, spend, and rate limits."""
    conn = psycopg2.connect(os.getenv("READONLY_DATABASE_URL"), connect_timeout=5)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT account_id, tier, monthly_spend, rate_limit
            FROM accounts
            WHERE account_id = %s;
            """,
            (account_id,),
        )
        row = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    if not row:
        return {"error": f"No account found for {account_id}"}
    return {"account_id": row[0], "tier": row[1], "monthly_spend": float(row[2]), "rate_limit": row[3]}

