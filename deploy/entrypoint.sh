#!/bin/sh
# Container entrypoint: wait for the DB, migrate, optionally collectstatic, then exec
# the service command. Used by the `web` service; worker/beat rely on compose
# depends_on healthchecks and do not migrate.
set -e

# Wait for Postgres (belt-and-suspenders alongside compose `depends_on: service_healthy`).
python - <<'PY'
import os
import sys
import time

import psycopg

url = os.environ["DATABASE_URL"]
for _ in range(60):
    try:
        psycopg.connect(url).close()
        break
    except Exception:
        time.sleep(1)
else:
    sys.exit("entrypoint: database not reachable")
PY

# Apply migrations on start unless disabled. Dev/D2/D3 leave this "1" (web self-migrates);
# prod (D5) sets MIGRATE_ON_START=0 and runs a dedicated one-shot `migrate` (scripts/deploy.sh)
# so concurrent replicas can't race the schema.
if [ "${MIGRATE_ON_START:-1}" != "0" ]; then
    python manage.py migrate --noinput
fi

if [ "${COLLECTSTATIC:-}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
