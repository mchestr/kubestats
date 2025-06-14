#! /usr/bin/env bash

set -e
set -x

# Run migrations
python -m alembic upgrade head

# Create initial data in DB
python kubestats/initial_data.py

# Start Uvicorn server
exec uvicorn kubestats.main:app --host 0.0.0.0 --port 8000
