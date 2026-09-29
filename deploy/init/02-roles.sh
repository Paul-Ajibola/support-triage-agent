#!/bin/bash
set -euo pipefail

: "${READONLY_DB_PASSWORD:?READONLY_DB_PASSWORD must be set}"

psql -v ON_ERROR_STOP=1 \
     -v ro_pw="$READONLY_DB_PASSWORD" \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" <<'EOSQL'

CREATE ROLE triage_readonly WITH LOGIN PASSWORD :'ro_pw';

GRANT CONNECT ON DATABASE triage_agent TO triage_readonly;
GRANT USAGE ON SCHEMA public TO triage_readonly;
GRANT SELECT ON accounts TO triage_readonly;

EOSQL
