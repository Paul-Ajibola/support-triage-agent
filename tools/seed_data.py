"""
seed_data.py

One-time local dev script: creates the `tickets` table in Postgres and
seeds it with a few fake historical tickets for testing ticket_lookup.
Not part of the live agent pipeline — throwaway test data only.

Run: python tools/seed_data.py
Requires: Postgres running, DATABASE_URL set in .env.local
"""

import psycopg2
import os
from dotenv import load_dotenv


load_dotenv(".env")

# make DB connection
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
# create cursor (messenger)
cur = conn.cursor()


cur.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    ticket_id TEXT UNIQUE,
    title TEXT,
    body TEXT,
    resolution TEXT,
    category TEXT
);
""")

sample_tickets = [
    ("T-1001", "Login fails after password reset", "User reset password but still gets 401 on login.", "Cleared cached session tokens; user re-logged in successfully.", "auth"),
    ("T-1002", "API rate limit hit unexpectedly", "Customer says they hit rate limit despite low usage.", "Found a misconfigured burst limit on their tier; adjusted config.", "billing"),
    ("T-1003", "Webhook not firing", "Webhook events stopped arriving after endpoint URL change.", "Endpoint URL had trailing slash mismatch; corrected URL.", "integration"),
]

for t in sample_tickets:
    cur.execute("""
    INSERT INTO tickets (ticket_id, title, body, resolution, category)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (ticket_id) DO NOTHING;
    """, t)

# save changes permanently
conn.commit()

# close curosr
cur.close()

# close DB connectio
conn.close()
print("Seeded tickets table.")


