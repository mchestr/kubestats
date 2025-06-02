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
exec python -m gunicorn \
    --bind 0.0.0.0:8000 \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --log-level $LOG_LEVEL \
    --access-logfile - \
    --error-logfile - \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s' \
    --name kubestats \
    --keep-alive 2 \
    --timeout 30 \
    --graceful-timeout 30 \
    kubestats.main:app
