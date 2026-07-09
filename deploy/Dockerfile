# syntax=docker/dockerfile:1
# Build context is the repo root; only backend/ is copied into the image.

# ---- Build stage: install deps into an isolated venv ----
FROM python:3.12-slim AS builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
# Copy requirements first so the pip layer caches across app-code changes.
COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- Final stage: slim runtime ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"
# WeasyPrint native deps (DVPS-9) — pango/cairo/gdk-pixbuf + fonts for Uzbek (Latin+Cyrillic)
# glyphs in PDFs. Only in the final stage; apt lists cleaned to keep the image small. Without
# these WeasyPrint imports but fails at render.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
        libgdk-pixbuf-2.0-0 libcairo2 libffi8 \
        fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# Run as a non-root user (security).
RUN groupadd --system app && useradd --system --gid app --no-create-home app
COPY --from=builder /venv /venv
COPY --chown=app:app backend/ ./
# Entrypoint lives outside /app so the dev bind-mount of ../backend:/app doesn't hide it.
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# STATIC_ROOT + MEDIA_ROOT are absent from the image (.dockerignore'd) — pre-create them
# owned by `app` so a first-init named volume inherits that ownership. Without this the
# volume mounts root-owned and `collectstatic`/uploads fail for the non-root user.
RUN mkdir -p /app/staticfiles /app/media && chown app:app /app/staticfiles /app/media
USER app
EXPOSE 8000
# Prod default; the dev compose overrides this with runserver (DVPS-4).
# psycopg[binary] bundles libpq, so no apt libpq-dev is needed here.
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]
