# maintainer-agent: API + bundled dashboard in one small image.
FROM python:3.11-slim

WORKDIR /app

# Install the package (package data: configs, fixtures, eval, dashboard).
COPY pyproject.toml README.md ./
COPY maintainer_agent ./maintainer_agent
RUN pip install --no-cache-dir .

# Entry point used when this image runs as a GitHub Action (read-only digest).
COPY docker/action-entrypoint.sh /app/action-entrypoint.sh
RUN chmod +x /app/action-entrypoint.sh

EXPOSE 8000
ENV MAINTAINER_AGENT_LOG_LEVEL=INFO

# Dashboard + JSON API. Binds $PORT when the host sets one (Render / HF Spaces / etc).
CMD maintainer-agent serve --host 0.0.0.0 --port ${PORT:-8000}
