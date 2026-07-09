#!/bin/sh
# First-run bootstrap for the backend stack. Idempotent — safe to re-run.
#   copy .env → build → start (web migrates on start) → seed reference data → super_admin.
set -eu

cd "$(dirname "$0")/.."  # repo root
COMPOSE="docker compose -f deploy/docker-compose.yml"

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "Created backend/.env from the template — review it (SECRET_KEY, passwords) before prod."
fi

echo "Building the image…"
$COMPOSE build

echo "Starting the stack (web runs migrate on startup)…"
$COMPOSE up -d --wait

echo "Seeding reference data (idempotent)…"
$COMPOSE exec -T web python manage.py seed_catalog
$COMPOSE exec -T web python manage.py seed_exercises
$COMPOSE exec -T web python manage.py seed_physical

echo "Creating the super_admin (idempotent)…"
$COMPOSE exec -T web python manage.py seed_admin || \
    echo "  (skipped — set DJANGO_SUPERUSER_PASSWORD in backend/.env, then: make createsuperuser)"

echo
echo "Ready. API → http://localhost:8000/api/v1/   admin → http://localhost:8000/admin/"
echo "Run the tests with: make test"
