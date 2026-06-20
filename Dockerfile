# Порядок backend — production image.
FROM python:3.12-slim

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY . .

# Production deps only (no dev group, no optional P1/P2 extras).
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["sh", "scripts/start.sh"]
