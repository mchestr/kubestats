# ==============================================================================
# Multi-stage build for minimal Python FastAPI application
# ==============================================================================

FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.11 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY ./kubestats ./kubestats
COPY ./alembic.ini ./docker-entrypoint.sh ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    mkdir -p /runtime/site-packages && \
    cp -r .venv/lib/python*/site-packages/* /runtime/site-packages/ && \
    cp -r .venv/bin/* /runtime/ && \
    cp -r kubestats alembic.ini /runtime/ && \
    cp docker-entrypoint.sh /runtime/ && \
    chmod +x /runtime/docker-entrypoint.sh

# ==============================================================================
FROM python:3.13-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

COPY --from=builder --chown=appuser:appuser /runtime/ /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/site-packages
WORKDIR /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
