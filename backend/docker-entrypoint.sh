#!/bin/sh
# Bring the schema up to date, then hand over to the process in CMD.
# No seeding: the tables start empty on purpose.
set -e

echo "waiting for postgres..."
python - <<'PY'
import os
import time

import psycopg

url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
for attempt in range(30):
    try:
        with psycopg.connect(url, connect_timeout=3):
            break
    except psycopg.OperationalError as exc:
        if attempt == 29:
            raise SystemExit(f"postgres unreachable: {exc}")
        time.sleep(2)
PY

echo "applying migrations..."
flask db upgrade

exec "$@"
