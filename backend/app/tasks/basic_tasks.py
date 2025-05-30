import datetime
import logging
import time

from app.celery_app import celery_app

# Set up logging
logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def create_log_entry(self, message: str, log_level: str = "INFO", duration: int = 5):
    """
    Basic task that creates log entries and simulates work.

    Args:
        message: The log message to create
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        duration: How long to simulate work (in seconds)

    Returns:
        dict: Task result with completion info
    """
    task_id = self.request.id
    start_time = datetime.datetime.now(datetime.UTC)

    # Log task start
    logger.info(f"Task {task_id} started: {message}")

    try:
        # Simulate work with progress updates
        for i in range(duration):
            time.sleep(1)
            progress = int((i + 1) / duration * 100)

            # Update task state with progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": duration,
                    "progress": progress,
                    "status": f"Processing step {i + 1} of {duration}",
                },
            )

            # Log progress
            logger.info(f"Task {task_id} progress: {progress}%")

        # Create the actual log entry based on specified level
        log_func = getattr(logger, log_level.lower(), logger.info)
        log_func(f"USER LOG: {message}")

        end_time = datetime.datetime.now(datetime.UTC)
        duration_seconds = (end_time - start_time).total_seconds()

        result = {
            "message": message,
            "log_level": log_level,
            "task_id": task_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "status": "completed",
        }

        logger.info(f"Task {task_id} completed successfully")
        return result

    except Exception as exc:
        logger.error(f"Task {task_id} failed: {str(exc)}")
        raise


@celery_app.task
def system_health_check():
    """
    Periodic task to check system health and log status.

    Returns:
        dict: System health status
    """
    start_time = datetime.datetime.now(datetime.UTC)

    try:
        # Check basic system status
        import psutil
        import redis

        from app.core.config import settings

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


@celery_app.task
def cleanup_old_logs():
    """
    Periodic task to clean up old log entries.
    This is a placeholder for future log cleanup functionality.

    Returns:
        dict: Cleanup results
    """
    start_time = datetime.datetime.now(datetime.UTC)

    logger.info("Starting log cleanup task")

    # Placeholder for actual cleanup logic
    # In a real implementation, this would clean up old log files or database entries

    result = {
        "timestamp": start_time.isoformat(),
        "cleaned_files": 0,  # Placeholder
        "freed_space_mb": 0,  # Placeholder
        "status": "completed",
    }

    logger.info(f"Log cleanup completed: {result}")
    return result
