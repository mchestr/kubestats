import os

from celery import Celery  # type: ignore[import-untyped]
from celery.schedules import crontab  # type: ignore[import-untyped]

from kubestats.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "kubestats.tasks.basic_tasks",
        "kubestats.tasks.discover_repositories",
        "kubestats.tasks.sync_repositories",
        "kubestats.tasks.scan_repositories",
        "kubestats.tasks.save_repository_metrics",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600 * 24 * 30,  # 1 month
    timezone=os.environ.get("TZ", "UTC"),
    enable_utc=True,
    result_extended=True,  # Store additional metadata
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Keep the original beat_schedule for task scheduling
    beat_schedule={
        "discover-repositories": {
            "task": "kubestats.tasks.discover_repositories.discover_repositories",
            "schedule": crontab(minute=1),  # Run every hour at minute 1
        },
        "sync_all_repositories": {
            "task": "kubestats.tasks.sync_repositories.sync_all_repositories",
            "schedule": crontab(minute=0, hour=0),  # Run daily at midnight
        },
        "cleanup-repository-workdirs": {
            "task": "kubestats.tasks.sync_repositories.cleanup_repository_workdirs",
            "schedule": crontab(minute=0, hour="*/2"),  # Run every 2 hours
        },
    },
)
