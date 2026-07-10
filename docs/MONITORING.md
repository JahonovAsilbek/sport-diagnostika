# Monitoring & logging

Lightweight monitoring for a single VPS — no Prometheus/Grafana. Logs go to stdout (Docker
`json-file`, rotated), errors to Sentry (opt-in), health to an external uptime monitor, and
disk/beat liveness to small dead-man switches. See `docs/DEPLOY.md` for the deploy itself.

## Health & uptime

`/api/v1/health/` (public, `AllowAny`) does a live `SELECT 1` + cache round-trip and returns:

- **200** `{"status":"ok","db":"ok","cache":"ok","time":…}` — healthy.
- **503** with the failing component named — so a monitor/LB reacts.

**Container healthchecks** (`docker compose ps` shows them): `web` (hits the endpoint), `db`,
`redis`, `worker` (`celery inspect ping`). `beat` has none — see *Beat liveness* below.

**External uptime monitor** — wire a free monitor to the public URL so you get alerted when the
VPS/app is down (the container healthcheck only restarts locally):

1. Create a monitor (UptimeRobot / Healthchecks.io / BetterStack) for
   `https://sport-diagnostika.uz/api/v1/health/`, interval 60s, alert on non-200 or timeout.
2. Route alerts to **email + Telegram** in the monitor's settings.

## Beat liveness

Celery Beat has no control API (and the slim image has no `ps`), so there's no container
healthcheck. Instead the `heartbeat` task (scheduled every 5 min by Beat) pings a **dead-man
switch**: set `HEALTHCHECK_PING_URL` (e.g. a Healthchecks.io check URL) in the server `.env`.
If Beat stops, the pings stop and that service alerts. Empty = disabled (the task no-ops).

## Resource monitoring

- Live: `docker stats` (CPU/mem per container) or `ctop`.
- **Disk** — `scripts/disk-alert.sh` warns past a threshold; run it from cron:
  ```cron
  */15 * * * * cd /home/deploy/sport && DISK_ALERT_THRESHOLD=85 \
    TELEGRAM_BOT_TOKEN=… TELEGRAM_CHAT_ID=… ./scripts/disk-alert.sh >> /var/log/disk-alert.log 2>&1
  ```
  With `TELEGRAM_*` set it sends a Telegram message; without, it exits non-zero so cron mails you.

## Logs

- Tail: `make prod-logs s=web` (or `worker` / `beat` / `nginx`).
- **Format:** prod logs are JSON, one object per line, with a `request_id`. Dev is plain text.
- **Correlation:** every request gets an `X-Request-ID` (generated, or a sanitized inbound one),
  echoed on the response and stamped on every log line. Celery tasks reuse the field with the
  task id. Trace one request across web + worker: `docker compose … logs | grep <request-id>`.
- **Rotation:** the `json-file` driver keeps 5 × 10 MB per container (`deploy/docker-compose.yml`).
- **No secrets/PII:** `django.db.backends` is at WARNING (no SQL/params); app code must not log
  request bodies; the audit `changes` JSON already excludes `password`/`last_login` and is stored
  in the DB, not logged.

## Error tracking (Sentry)

Opt-in — inert unless `SENTRY_DSN` is set (so dev/CI never send events). Covers **web + worker +
beat** (initialized once per process in `config/settings/prod.py`).

1. Create a Sentry project (Python/Django); copy its DSN.
2. In the server `backend/.env`: `SENTRY_DSN=…`, `SENTRY_ENVIRONMENT=production`,
   `SENTRY_RELEASE=<git-sha>` (set automatically if you export it in `scripts/deploy.sh`),
   optionally `SENTRY_TRACES_SAMPLE_RATE` (default `0.0` = errors only, free-tier friendly).
3. `./scripts/deploy.sh` (restart). Trigger a test error in web and in a Celery task; confirm both
   appear in Sentry.

**PII posture:** `send_default_pii=False` (no cookies/IP/user id) and `max_request_body_size="never"`
(request bodies — incl. passwords — are never captured). Sentry's EventScrubber also redacts
`password`/`authorization`/`secret` keys by default.

## Alert routing

- **Uptime / health** → the external monitor (email + Telegram).
- **Beat down** → the Healthchecks.io dead-man switch (email + Telegram).
- **Disk** → `scripts/disk-alert.sh` → Telegram (or cron mail).
- **Application errors** → Sentry (its own email/Slack/Telegram integrations).

Telegram setup: create a bot via `@BotFather` → `TELEGRAM_BOT_TOKEN`; get your chat id (message
the bot, then `getUpdates`) → `TELEGRAM_CHAT_ID`.

## What each alert means (first response)

| Alert | Likely cause | First step |
|---|---|---|
| health 503 `db:down` | Postgres down / disk full | `docker compose … ps db`, `logs db`; check disk |
| health 503 `cache:down` | Redis down | `logs redis`; restart |
| health timeout / no response | web/nginx down, TLS/cert issue | `ps`, `logs web nginx`; `docs/DEPLOY.md` cert steps |
| beat heartbeat missed | Beat crashed | `logs beat`; it should auto-`restart` — check why it died |
| disk alert | logs/backups/pgdata growth | `du -sh`, prune old `backups/`, check log rotation |
| Sentry spike | a real bug | triage by `request_id`; correlate with logs |
