# maintainer-agent: API + bundled dashboard in one small image.
# Multi-stage build: (1) compile the React/Vite frontend, (2) install the Python package.

# --- Stage 1: Build frontend ---
FROM node:18-slim AS frontend
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN npm ci --silent
COPY web/ ./
RUN npm run build

# --- Stage 2: Python backend ---
FROM python:3.11-slim

WORKDIR /app

# Install the package (package data: configs, fixtures, eval, dashboard).
COPY pyproject.toml README.md ./
COPY maintainer_agent ./maintainer_agent

# Copy the compiled frontend into the package's static dir so it ships with pip.
COPY --from=frontend /web/dist ./maintainer_agent/api/static

RUN pip install --no-cache-dir .

# Entry point used when this image runs as a GitHub Action (read-only digest).
COPY docker/action-entrypoint.sh /app/action-entrypoint.sh
RUN chmod +x /app/action-entrypoint.sh

EXPOSE 8000
ENV MAINTAINER_AGENT_LOG_LEVEL=INFO

# Dashboard + JSON API. Binds $PORT when the host sets one (Render / Cloud Run / etc).
CMD maintainer-agent serve --host 0.0.0.0 --port ${PORT:-8000}
