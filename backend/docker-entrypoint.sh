#! /usr/bin/env bash

set -e
set -x

# Run migrations
python -m alembic upgrade head

# Create initial data in DB
python kubestats/initial_data.py

# Start Gunicorn with inline configuration
exec fastapi run kubestats/main.py --port 8000
