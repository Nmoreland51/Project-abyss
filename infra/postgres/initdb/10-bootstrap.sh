#!/bin/sh
# Runs once, on first initialisation of an empty data volume (postgres image entrypoint).
set -eu
: "${MIGRATOR_PASSWORD:?MIGRATOR_PASSWORD must be set}"
: "${RUNTIME_PASSWORD:?RUNTIME_PASSWORD must be set}"
psql -v ON_ERROR_STOP=1 -v migrator_pw="$MIGRATOR_PASSWORD" -v runtime_pw="$RUNTIME_PASSWORD" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /bootstrap/roles.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -c "ALTER DATABASE \"$POSTGRES_DB\" OWNER TO app_migrator"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /bootstrap/database.sql
