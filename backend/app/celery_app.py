from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.basic_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600 * 24 * 30,  # 1 month
    timezone="UTC",
    enable_utc=True,
    result_extended=True,  # Store additional metadata
    worker_send_task_events=True,
    task_send_sent_event=True,
)
