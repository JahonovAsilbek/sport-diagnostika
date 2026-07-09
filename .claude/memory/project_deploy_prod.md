---
name: project_deploy_prod
description: Prod topology (nginx + gunicorn) gotchas — root-owned volumes, compose !override, XFF, HTTP-only pre-TLS
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

**D5 forward-flag:** the container healthcheck hits gunicorn directly (`127.0.0.1:8000`), so it
never sends `X-Forwarded-Proto: https` — with TLS, do the http→https redirect in an nginx `:80`
block and keep Django's `SECURE_SSL_REDIRECT` off (or exempt `/api/v1/health/`), else the
healthcheck 301-loops even with certs.
