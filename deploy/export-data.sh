#!/bin/sh
# Run on your laptop, from the repository root, with the local stack running.
# Produces deploy/out/website.dump (full schema + data, including alembic_version)
# and deploy/out/uploads.tar.gz (only the files media_asset rows point to).
set -e

out=deploy/out
mkdir -p "$out"

docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner' > "$out/website.dump"

docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select filename from media_asset"' > "$out/uploads.txt"
tar -czf "$out/uploads.tar.gz" -C backend/uploads -T "$out/uploads.txt"

echo "wrote $out/website.dump and $out/uploads.tar.gz ($(wc -l < "$out/uploads.txt" | tr -d ' ') files)"
