# ==============================================================================
# Multi-stage build for minimal Python FastAPI application
# Stage 1: Builder (python:3.11-slim)
# Stage 2: Runtime (gcr.io/distroless/python3-debian12)
# ==============================================================================

# Stage 1: Builder stage
FROM python:3.11-slim AS builder

# Set all environment variables in one layer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /app

# Install system dependencies and uv in one layer
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/

# Copy all source files and install dependencies in one optimized sequence
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY ./kubestats /app/kubestats
COPY ./alembic.ini ./docker-entrypoint.sh /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    # Create runtime directory structure
    mkdir -p /runtime/site-packages && \
    mkdir -p /runtime/tmp && \
    chmod 777 /runtime/tmp && \
    # Copy Python packages and binaries
    cp -r /app/.venv/lib/python*/site-packages/* /runtime/site-packages/ && \
    cp -r /app/.venv/bin/* /runtime/ && \
    # Copy application files
    cp -r /app/kubestats /runtime/ && \
    # Copy configuration files
    cp /app/alembic.ini /runtime/ && \
    # Copy and set executable permissions for entrypoint
    cp /app/docker-entrypoint.sh /runtime/ && \
    chmod +x /runtime/docker-entrypoint.sh

# ==============================================================================
# Stage 2: Runtime stage using distroless
FROM gcr.io/distroless/python3-debian12

# Copy all runtime files and set environment variables in minimal layers
COPY --from=builder /runtime/site-packages /app/site-packages
COPY --from=builder /runtime/ /app/
COPY --from=builder /runtime/tmp /tmp/

# Create a writable directory for Celery Beat schedule file
# Note: We can't use mkdir in distroless, so we create it in the builder stage
# Set all environment variables and configurations in one layer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/site-packages

WORKDIR /app
USER nonroot
EXPOSE 8000

# Run the application
ENTRYPOINT ["docker-entrypoint.sh"]
