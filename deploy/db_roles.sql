-- read-only role used by tools/account_context_db.py
-- Run AFTER tools/seed_accounts.py has created the accounts table:
--  docker compose exec -T postgres psql -U triage -d triage_agent < deploy/db_role.sql


DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'triage_readonly') THEN
        CREATE ROLE triage_readonly WITH LOGIN PASSWORD 'readonly_pw_change_me';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE triage_agent TO triage_readonly;
GRANT USAGE ON SCHEMA public TO triage_readonly;
GRANT SELECT ON accounts TO triage_readonly;
REVOKE INSERT, UPDATE, DELETE ON accounts FROM triage_readonly;

