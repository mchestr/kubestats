# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many requests, to help prevent memory leaks
preload_app = True

# Logging
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "kubestats-backend"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in the future)
keyfile = None
certfile = None

# Performance tuning
keepalive = 2
timeout = 30
graceful_timeout = 30
