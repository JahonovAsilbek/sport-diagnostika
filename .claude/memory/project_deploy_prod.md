---
name: project_deploy_prod
description: Prod + TLS topology (nginx + gunicorn + certbot) gotchas — root-owned volumes, compose !override, XFF, cert bootstrap, one-shot migrate
metadata:
  type: project
---

Prod profile = `deploy/docker-compose.prod.yml` overlaid on the base:
`docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml …`
(`make prod-up`). nginx `:80` → gunicorn `web`; SPA + `/static/` + `/media/` from volumes.
Built in D3 (DVPS-12/13). See [[project_dev_toolchain]].

Non-obvious facts (bit us / verified in D3):

- **Root-owned named volumes.** `backend/staticfiles/` + `backend/media/` are `.dockerignore`d
  and don't exist in the image, so a named volume mounted at `/app/staticfiles` or `/app/media`
  is created **root:root** — but the container runs `USER app`, so `collectstatic`/uploads fail.
  Fix lives in `deploy/Dockerfile`: `mkdir -p /app/staticfiles /app/media && chown app:app …`
  **before** `USER app` (first-init copies that ownership into the fresh volume).

- **Compose can't remove a base list entry additively.** To drop the dev `../backend:/app`
  source mount in the prod overlay, use the merge tags `volumes: !override` (replace the whole
  list) and `ports: !reset []`. Needs Compose ≥ 2.24 (repo runs 5.x). A plain override just
  appends, leaving the source mount in place.

- **X-Forwarded-For must be OVERWRITTEN, not appended.** `apps/audit/context.client_ip` reads
  the **first** hop (`split(",")[0]`). nginx is the sole edge, so `proxy_set_header
  X-Forwarded-For $remote_addr;` — using `$proxy_add_x_forwarded_for` (appends) would let a
  client spoof the audit IP.

- **HTTP-only until D5 (TLS).** `prod.py` gates HTTPS hardening behind
  `env.bool("SECURE_SSL_REDIRECT", default=True)` (SSL redirect + Secure cookies + HSTS all
  follow it). The prod overlay sets `SECURE_SSL_REDIRECT=False` so the pre-TLS stack doesn't
  301-loop and admin/healthcheck work over http. `ALLOWED_HOSTS` **must** keep `127.0.0.1`
  (the container healthcheck sends `Host: 127.0.0.1` and `DEBUG=False` rejects unlisted hosts).

- **`nginx -t` resolves upstreams.** It fails with "host not found in upstream web:8000" unless
  `web` is resolvable — so a `--no-deps` test alone fails on DNS, not syntax. Validate with a
  `docker run --add-host web:127.0.0.1 … nginx -t`.

- **SPA `/` → 404 until the F-blocks** populate `frontend/dist` (bind-mounted read-only into
  nginx). API/admin/static/media work meanwhile.

**TLS (D5, DVPS-15/16)** — a 3rd overlay `docker-compose.tls.yml` on top of base+prod
(`-f base -f prod -f tls`), **certbot + webroot** (keeps the hand-written nginx; not
acme-companion). `deploy/nginx.tls.conf` + `scripts/{init-letsencrypt,deploy}.sh` +
`docs/DEPLOY.md`. Verified facts:

- **Healthcheck vs SSL redirect.** The container healthcheck hits gunicorn directly (no
  `X-Forwarded-Proto`), so with `SECURE_SSL_REDIRECT=True` it 301-loops. Fix:
  `SECURE_REDIRECT_EXEMPT=[r"^api/v1/health/$"]` in prod.py (SecurityMiddleware lstrips "/" +
  `re.search`). nginx does the real http→https redirect at `:80`; the tls overlay flips web
  `SECURE_SSL_REDIRECT=True` (HSTS/secure cookies back on).

- **Publish NOTHING but nginx on the VPS.** The base compose maps `5432`/`6379` for host-venv
  dev; `prod.yml` `!reset []`s `db.ports` + `redis.ports` or the datastores are internet-exposed.

- **HSTS must be set at nginx**, not only Django — Django only emits it on `/api`+`/admin`; the
  nginx-served SPA/`/static`/`/media` need it for preload. `add_header … Strict-Transport-Security`
  at the `:443` server + `proxy_hide_header Strict-Transport-Security` on proxied locations (a
  location with its own `add_header`, e.g. `/media/`, must re-assert it — nginx doesn't inherit).

- **One-shot migrate.** `entrypoint.sh` gates migrate behind `MIGRATE_ON_START` (default "1");
  prod web sets "0"; `deploy.sh` runs `run --rm -e MIGRATE_ON_START=0 -e COLLECTSTATIC=0 web …
  migrate` (COLLECTSTATIC=0 too — the entrypoint runs collectstatic regardless of the migrate gate).

- **Cert bootstrap chicken-egg.** nginx won't boot without the cert it references, but certbot
  needs nginx serving the ACME webroot. `init-letsencrypt.sh` writes a dummy self-signed cert →
  nginx up → certbot `certonly --webroot` (STAGING=1 first). The certbot service's *entrypoint* is
  a renew loop, and `docker compose run` overrides *command* not entrypoint → one-shots MUST pass
  `--entrypoint`.

- **Worker sizing.** `deploy/gunicorn.conf.py` (mounted, `gunicorn -c`) = `(2*cores)+1`,
  `WEB_CONCURRENCY` override. Dropping `--workers` and relying on a bare `WEB_CONCURRENCY` would
  silently fall to 1 worker if unset.

- **Verify TLS config by BOOTING nginx**, not just `nginx -t` — `-t` misses `listen [::]:443`
  IPv6-bind failures + accepts the cert-missing case differently. Use a throwaway self-signed cert
  under `$HOME` (colima only shares `$HOME`, **not** `/private/tmp` scratchpad) + `--add-host
  web:127.0.0.1`, then `docker run -d …` and assert the container stays `Up`.
