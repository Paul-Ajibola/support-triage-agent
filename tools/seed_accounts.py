# tools/seed_accounts.py
"""
seed_accounts.py

One-time local dev script: creates the `accounts` table in Postgres and
seeds it with one fake account (ACC-001) for testing account_context_db.
Not part of the live agent pipeline — throwaway test data only.

Run: python tools/seed_accounts.py
Requires: Postgres running, DATABASE_URL set in .env.local
"""

import psycopg2, os
from dotenv import load_dotenv
load_dotenv(".env")

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    tier TEXT,
    monthly_spend NUMERIC,
    rate_limit INT
);
""")
cur.execute("""
    INSERT INTO accounts (account_id, tier, monthly_spend, rate_limit)
    VALUES ('ACC-001', 'enterprise', 4200.00, 10000)
    ON CONFLICT (account_id) DO NOTHING;
""")
conn.commit()
cur.close()
conn.close()
print("Seeded accounts table.")