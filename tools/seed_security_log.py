"""
seed_security_log.py

one-time local dev script: creates the `security_audit_log` table in 
Postgres so agent/security/audit_log.py has somewhere to write to.
Not part of the live agent pipeline -- run once per environment.
"""


import psycopy2
import os
from dotenv import load_dotenv



load_dotenv(".env")


conn = psycopy2.connect(os.getenv("DATABASR_URL"))
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS security_audit_log (
id SERIAL PRIMARY KEY,
ticket_id TEXT,
event_type TEXT NOT NULL,
detail TEXT,
ticket_body_snippet TEXT,
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
""")
conn.commit()
cur.close()
conn.close()
print("Seeded security_audit_log table.")