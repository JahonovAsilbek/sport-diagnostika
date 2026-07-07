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
WORKDIR /app
# Run as a non-root user (security).
RUN groupadd --system app && useradd --system --gid app --no-create-home app
COPY --from=builder /venv /venv
COPY --chown=app:app backend/ ./
USER app
EXPOSE 8000
# Prod default; the dev compose overrides this with runserver (DVPS-4).
# psycopg[binary] bundles libpq, so no apt libpq-dev is needed here.
CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000"]
