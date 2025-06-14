#! /usr/bin/env bash

set -e
set -x

# Run migrations
python -m alembic upgrade head

# Create initial data in DB
python kubestats/initial_data.py

# Calculate number of workers
WORKERS=${WORKERS:-$(($(nproc) * 2 + 1))}
LOG_LEVEL=${LOG_LEVEL:-info}

# Start Gunicorn with inline configuration
exec fastapi run kubestats/main.py --port 80
