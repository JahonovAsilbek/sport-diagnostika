#!/bin/sh
# Idempotent production deploy (D5 / DVPS-15). Run on the VPS from the repo root.
#   git pull → build → one-shot migrate → up → prune.
# Assumes the first cert already exists (scripts/init-letsencrypt.sh). Secrets live only in
# backend/.env on the server (chmod 600) — never in the image or the repo.
set -eu

cd "$(dirname "$0")/.."  # repo root
COMPOSE="docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml -f deploy/docker-compose.tls.yml"

echo "### pulling latest…"
git pull --ff-only

echo "### building the image…"
$COMPOSE build

# One-shot schema migration in a throwaway container BEFORE (re)starting web. MIGRATE_ON_START=0
# stops the entrypoint from also migrating (no double run); COLLECTSTATIC=0 skips the redundant
# collectstatic here (the web service still runs it on startup). A single writer of the schema
# → scaling web beyond one replica never races migrations.
echo "### running migrations (one-shot)…"
$COMPOSE run --rm -e MIGRATE_ON_START=0 -e COLLECTSTATIC=0 web python manage.py migrate --noinput

echo "### starting/refreshing the stack…"
$COMPOSE up -d --remove-orphans

echo "### pruning dangling images…"
docker image prune -f

echo "Done. Check: curl -I https://sport-diagnostika.uz/api/v1/health/"
