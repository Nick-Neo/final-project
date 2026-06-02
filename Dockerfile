# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies into a separate layer so they're cached
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (includes migrations/)
COPY . .

# Don't run as root
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Explicit module:object so `flask db upgrade` finds the app directly
ENV FLASK_APP=ecom_app:app

# ACA routes to this port — set ingress target port to 8000 in ACA config
EXPOSE 8000

# gunicorn loads gunicorn.conf.py, whose post_fork hook configures Azure Monitor
# per worker — that's where telemetry export actually works.
# `exec` replaces the shell so gunicorn receives SIGTERM directly on stop.
# Override workers via GUNICORN_WORKERS env var without rebuilding the image.
CMD exec gunicorn \
    -c gunicorn.conf.py \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    ecom_app:app