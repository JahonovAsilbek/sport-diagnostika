# SPORT-DIAGNOSTIKA.UZ — dev workflow. Run every target from the repo root.
# The stack + app commands go through docker compose; test/lint/format use the local
# venv (dev tooling isn't in the runtime image — see backend/requirements-dev.txt).
COMPOSE := docker compose -f deploy/docker-compose.yml
# Prod overlay: gunicorn + nginx, no source mount (deploy/docker-compose.prod.yml).
PROD    := docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml
MANAGE  := $(COMPOSE) exec -T web python manage.py
VENV    := backend/.venv/bin

.DEFAULT_GOAL := help
.PHONY: help bootstrap build up down logs ps migrate makemigrations shell \
        seed createsuperuser psql test lint format \
        prod-build prod-up prod-down prod-logs

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

bootstrap: ## First run: .env → build → up (auto-migrates) → seed → super_admin
	./scripts/bootstrap.sh

build: ## Build the backend image
	$(COMPOSE) build

up: ## Start the stack (db, redis, web, worker, beat); web migrates on start
	$(COMPOSE) up -d

down: ## Stop the stack
	$(COMPOSE) down

logs: ## Tail logs — `make logs s=web` to filter a service
	$(COMPOSE) logs -f $(s)

ps: ## Stack status
	$(COMPOSE) ps

migrate: ## Apply migrations
	$(MANAGE) migrate

makemigrations: ## Create migrations
	$(MANAGE) makemigrations

shell: ## Django shell (web container)
	$(COMPOSE) exec web python manage.py shell

seed: ## Load reference data — catalog → exercises → physical norms (idempotent)
	$(MANAGE) seed_catalog
	$(MANAGE) seed_exercises
	$(MANAGE) seed_physical

createsuperuser: ## Create the super_admin (idempotent; uses DJANGO_SUPERUSER_PASSWORD)
	$(MANAGE) seed_admin

psql: ## psql into the db container
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

test: ## Run the test suite (local venv; needs the stack up for Postgres)
	cd backend && .venv/bin/pytest -q

lint: ## Ruff lint
	$(VENV)/ruff check backend

format: ## Ruff format + autofix
	$(VENV)/ruff format backend
	$(VENV)/ruff check --fix backend

prod-build: ## Build images for the prod profile (gunicorn + nginx)
	$(PROD) build

prod-up: ## Start the prod profile — nginx on :80, gunicorn web (HTTP-only until D5/TLS)
	$(PROD) up -d

prod-down: ## Stop the prod profile
	$(PROD) down

prod-logs: ## Tail prod logs — `make prod-logs s=nginx` to filter a service
	$(PROD) logs -f $(s)
