CREATE TABLE IF NOT EXISTS tickets (
    id          SERIAL PRIMARY KEY,
    ticket_id   TEXT UNIQUE,
    title       TEXT,
    body        TEXT,
    resolution  TEXT,
    category    TEXT
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id     TEXT PRIMARY KEY,
    tier           TEXT,
    monthly_spend  NUMERIC,
    rate_limit     INT
);

CREATE TABLE IF NOT EXISTS security_audit_log (
    id                   SERIAL PRIMARY KEY,
    ticket_id            TEXT,
    event_type           TEXT NOT NULL,
    detail               TEXT,
    ticket_body_snippet  TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);