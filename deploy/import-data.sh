#!/bin/sh
# Run on the server, from the repository root, after copying deploy/out/ there.
# Replaces whatever is in the server database with the dump. Destructive.
set -e

in=deploy/out
test -f "$in/website.dump" || { echo "missing $in/website.dump"; exit 1; }

docker compose up -d db
until docker compose exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; do sleep 1; done

docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$in/website.dump"

mkdir -p backend/uploads
tar -xzf "$in/uploads.tar.gz" -C backend/uploads

echo "data restored; now run: docker compose up -d --build"
