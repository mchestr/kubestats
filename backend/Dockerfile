# ==============================================================================
# Multi-stage build for minimal Python FastAPI application
# Stage 1: Builder (python:3.13-slim)
# Stage 2: Runtime (python:3.13-slim)
# ==============================================================================

# Stage 1: Builder stage
FROM python:3.13-slim AS builder

# Set environment variables and install system dependencies in one layer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /app

# Install system dependencies and copy uv binary in one layer
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /uvx /bin/

# Copy dependency files and install dependencies
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy source files and build final runtime structure
COPY ./kubestats ./kubestats
COPY ./alembic.ini ./docker-entrypoint.sh ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    # Prepare optimized runtime structure
    mkdir -p /runtime/site-packages && \
    # Copy all necessary files in one operation
    cp -r .venv/lib/python*/site-packages/* /runtime/site-packages/ && \
    cp -r .venv/bin/* /runtime/ && \
    cp -r kubestats alembic.ini /runtime/ && \
    cp docker-entrypoint.sh /runtime/ && \
    chmod +x /runtime/docker-entrypoint.sh

# ==============================================================================
# Stage 2: Minimal runtime stage
FROM python:3.13-slim

# Create user and set up environment in one layer
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy runtime files and set permissions
COPY --from=builder --chown=appuser:appuser /runtime/ /app/

# Set environment variables, working directory, and user
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/site-packages
WORKDIR /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
