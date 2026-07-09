# Production deploy — sport-diagnostika.uz

The runbook for deploying the platform to a VPS with TLS. Everything runs as three stacked
compose files: `docker-compose.yml` (base) + `docker-compose.prod.yml` (gunicorn, no source
mount, datastores unpublished) + `docker-compose.tls.yml` (nginx `:443`, Let's Encrypt certbot,
HTTPS hardening). Secrets live only in `backend/.env` **on the server** — never in the image or
the repo.

> The Vue SPA (F-blocks) isn't built yet, so `/` serves a 404 until `frontend/dist` exists. The
> API (`/api/`), admin (`/admin/`), and health check work regardless.

The full compose invocation (aliased as `$C` below):

```sh
C="docker compose -f deploy/docker-compose.yml \
                  -f deploy/docker-compose.prod.yml \
                  -f deploy/docker-compose.tls.yml"
```

## 1. Prerequisites

- A VPS (≥ 2 vCPU, ≥ 2 GB RAM), Ubuntu 22.04/24.04.
- A domain (`sport-diagnostika.uz`) whose DNS you control.

## 2. Provision the VPS

```sh
# Docker Engine + compose plugin
curl -fsSL https://get.docker.com | sh
docker compose version          # must be >= 2.24 (the !override / !reset merge tags)

# A non-root deploy user in the docker group
sudo adduser deploy && sudo usermod -aG docker deploy

# Firewall: SSH + HTTP + HTTPS only. Postgres/Redis are NEVER published (the prod overlay
# resets their host ports); the app reaches them over the internal `sport` network.
sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

Clone the repo as `deploy`: `git clone <repo-url> ~/sport && cd ~/sport`.

## 3. DNS

Point both hosts at the VPS IPv4 (add `AAAA` only if the VPS has IPv6 — the nginx config keeps
`listen [::]`; drop those lines if it doesn't):

```
A   sport-diagnostika.uz       → <VPS IPv4>
A   www.sport-diagnostika.uz   → <VPS IPv4>
```

Verify before requesting certs: `dig +short sport-diagnostika.uz` returns the VPS IP.

## 4. Server secrets (`backend/.env`)

```sh
cp backend/.env.example backend/.env
chmod 600 backend/.env
```

Set at minimum:

- `SECRET_KEY` — generate: `python3 -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
- `DJANGO_SETTINGS_MODULE=config.settings.prod`, `DEBUG=False`
- `ALLOWED_HOSTS=127.0.0.1,sport-diagnostika.uz,www.sport-diagnostika.uz` (**keep `127.0.0.1`** — the container healthcheck needs it)
- `CSRF_TRUSTED_ORIGINS=https://sport-diagnostika.uz,https://www.sport-diagnostika.uz`
- `WEB_CONCURRENCY` — optional; defaults to `(2 × cores) + 1`. Pin it on a shared box.
- Strong `POSTGRES_PASSWORD` (keep `DATABASE_URL` in sync) and `DJANGO_SUPERUSER_PASSWORD`.

`.env` is git-ignored and `.dockerignore`d (`**/.env`) — it never enters the image.

## 5. First certificate (staging → production)

Let's Encrypt rate-limits real certs, so validate the flow with a **staging** cert first.

```sh
$C build

# Staging first — untrusted cert, browsers warn, but proves DNS + the webroot challenge work.
DOMAIN=sport-diagnostika.uz LETSENCRYPT_EMAIL=admin@sport-diagnostika.uz STAGING=1 \
  ./scripts/init-letsencrypt.sh

# Once https responds (ignore the staging warning), switch to a trusted cert:
DOMAIN=sport-diagnostika.uz LETSENCRYPT_EMAIL=admin@sport-diagnostika.uz STAGING=0 \
  ./scripts/init-letsencrypt.sh
```

`init-letsencrypt.sh` drops a throwaway self-signed cert so nginx can boot, serves the ACME
HTTP-01 challenge on `:80`, then swaps in the real cert and reloads nginx. The `STAGING=0` re-run
deletes the staging lineage first, so there's no duplicate-cert rate-limit hit.

## 6. First deploy

```sh
./scripts/deploy.sh      # git pull → build → one-shot migrate → up -d → prune

# Seed the reference data + super_admin (idempotent):
$C exec web python manage.py seed_catalog
$C exec web python manage.py seed_exercises
$C exec web python manage.py seed_physical
$C exec web python manage.py seed_admin
```

Migrations run as a **dedicated one-shot job** inside `deploy.sh` (not on web start:
`MIGRATE_ON_START=0`), so scaling `web` beyond one replica can never race the schema.

## 7. Verify

```sh
curl -I  http://sport-diagnostika.uz                    # 301 → https
curl -sI https://sport-diagnostika.uz/api/v1/health/    # 200 + Strict-Transport-Security
$C ps                                                    # web healthy; only nginx on :80/:443
$C run --rm --entrypoint certbot certbot renew --dry-run # renewal wiring OK
```

Also confirm admin login works over https and HSTS is present on `/` (not just `/api`).

## 8. Ongoing operations

- **Redeploy:** `./scripts/deploy.sh` (pull → build → migrate → up → prune).
- **Cert renewal:** automatic — the `certbot` container runs `certbot renew` every 12 h; nginx
  reloads every 6 h to pick up a renewed cert. No cron needed.
- **Worker sizing:** `deploy/gunicorn.conf.py` sizes to cores by default; set `WEB_CONCURRENCY`
  to override.
- **Rollback:** `git checkout <prev-sha> && ./scripts/deploy.sh`. Migrations are forward-only —
  if a migration must be undone, restore the database from a backup (D6).

## 9. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| nginx won't start (`cannot load certificate`) | No cert yet — run `scripts/init-letsencrypt.sh`. |
| Health check 400 / web never healthy | `ALLOWED_HOSTS` is missing `127.0.0.1`. |
| Only 1 gunicorn worker | `WEB_CONCURRENCY` set to 1, or a 0-core reading — check `deploy/gunicorn.conf.py`. |
| ACME challenge 404 | DNS not pointing at the VPS yet, or `:80` blocked by the firewall. |
| nginx crash on boot, `Address family not supported` | VPS has no IPv6 — remove the `listen [::]` lines from `deploy/nginx.tls.conf`. |
