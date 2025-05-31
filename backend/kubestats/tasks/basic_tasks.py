import datetime
import logging
from typing import Any

from kubestats.celery_app import celery_app

# Set up logging
logger = logging.getLogger(__name__)


@celery_app.task  # type: ignore[misc]
def system_health_check() -> dict[str, Any]:
    """
    Periodic task to check system health and log status.

    Returns:
        dict: System health status
    """
    start_time = datetime.datetime.now(datetime.UTC)

    try:
        # Check basic system status
        import psutil  # type: ignore
        import redis  # type: ignore

        from kubestats.core.config import settings

        # Check Redis connection
        r = redis.Redis.from_url(settings.REDIS_URL)
        redis_status = r.ping()

        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        health_data = {
            "timestamp": start_time.isoformat(),
            "redis_status": "healthy" if redis_status else "unhealthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "status": "healthy",
        }

        logger.info(f"System health check completed: {health_data}")
        return health_data

    except Exception as exc:
        logger.error(f"System health check failed: {str(exc)}")
        return {
            "timestamp": start_time.isoformat(),
            "status": "unhealthy",
            "error": str(exc),
        }
