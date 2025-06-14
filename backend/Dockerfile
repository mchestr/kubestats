FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential curl git && rm -rf /var/lib/apt/lists/*

# Copy application code and dependencies
COPY pyproject.toml ./
COPY ./kubestats ./kubestats

# Install Python dependencies
RUN pip install --no-cache-dir .
COPY ./alembic.ini ./docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
