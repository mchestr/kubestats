# ==============================================================================
# Multi-stage build for minimal Python FastAPI application
# Stage 1: Builder (python:3.11-slim)
# Stage 2: Runtime (gcr.io/distroless/python3-debian12)
# ==============================================================================

# Stage 1: Builder stage
FROM python:3.13-slim AS builder

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

COPY ./app /app/app 
COPY ./scripts /app/scripts 
COPY ./alembic.ini ./gunicorn.conf.py /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev && \
    mkdir -p /runtime/site-packages && \
    mkdir -p /runtime/tmp && \
    chmod 777 /runtime/tmp && \
    cp -r /app/.venv/lib/python*/site-packages/* /runtime/site-packages/ && \
    cp -r /app/app /runtime/ && \
    cp -r /app/scripts /runtime/ && \
    cp /app/alembic.ini /runtime/ && \
    cp /app/gunicorn.conf.py /runtime/

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

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import requests; requests.get('http://localhost:8000/api/v1/utils/health-check/', timeout=10)"]

# Run the application
ENTRYPOINT ["python", "-m", "gunicorn"]
CMD ["-c", "gunicorn.conf.py", "app.main:app"]
