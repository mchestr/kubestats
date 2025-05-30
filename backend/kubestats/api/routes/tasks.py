import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from kubestats.api.deps import get_current_active_superuser
from kubestats.celery_app import celery_app
from kubestats.crud import get_worker_stats_by_id
from kubestats.models import User
from kubestats.tasks.basic_tasks import create_log_entry, system_health_check

router = APIRouter()
logger = logging.getLogger(__name__)


class TaskTriggerRequest(BaseModel):
    message: str
    log_level: str = "INFO"
    duration: int = 5


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None
    traceback: str | None = None
    date_done: str | None = None
    name: str | None = None
    worker: str | None = None
    retries: int | None = None

    @field_validator("result", mode="before")
    @classmethod
    def serialize_exception_result(cls, v: Any) -> Any:
        """Convert exception objects to string representation before validation."""
        if isinstance(v, Exception):
            return f"{type(v).__name__}: {str(v)}"
        return v


class WorkerStatsResponse(BaseModel):
    worker_id: str
    worker_name: str
    status: str
    uptime: int | None = None
    pid: int | None = None
    clock: int | None = None
    prefetch_count: int | None = None
    pool: dict[str, Any] | None = None
    broker: dict[str, Any] | None = None
    total_tasks: dict[str, Any] | None = None
    rusage: dict[str, Any] | None = None


class PeriodicTaskResponse(BaseModel):
    name: str
    task: str
    schedule: str
    enabled: bool = True
    last_run_at: str | None = None
    total_run_count: int | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None


@router.post("/trigger", response_model=TaskResponse)
def trigger_log_task(
    task_request: TaskTriggerRequest,
    current_user: User = Depends(get_current_active_superuser),
) -> TaskResponse:
    """
    Trigger a basic logging task (superuser only).
    """
    try:
        result = create_log_entry.delay(
            message=task_request.message,
            log_level=task_request.log_level,
            duration=task_request.duration,
        )

        logger.info(f"Task triggered by user {current_user.id}: {result.id}")

        return TaskResponse(
            task_id=result.id,
            status="PENDING",
            message=f"Task triggered successfully: {task_request.message}",
        )
    except Exception as e:
        logger.error(f"Error triggering task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger task: {str(e)}")


@router.post("/health-check", response_model=TaskResponse)
def trigger_health_check(
    current_user: User = Depends(get_current_active_superuser),
) -> TaskResponse:
    """
    Trigger a system health check task (superuser only).
    """
    try:
        result = system_health_check.delay()

        logger.info(f"Health check triggered by user {current_user.id}: {result.id}")

        return TaskResponse(
            task_id=result.id,
            status="PENDING",
            message="Health check task triggered successfully",
        )
    except Exception as e:
        logger.error(f"Error triggering health check: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger health check: {str(e)}"
        )


@router.get(
    "/status/{task_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=TaskStatusResponse,
)
def get_task_status(
    task_id: str,
) -> TaskStatusResponse:
    """
    Get status of a specific task (superuser only).
    """
    try:
        result = celery_app.AsyncResult(task_id)

        return TaskStatusResponse(
            task_id=task_id,
            status=result.status,
            result=result.result,
            traceback=result.traceback,
            date_done=result.date_done.isoformat() if result.date_done else None,
            name=getattr(result, "name", None),
            worker=getattr(result, "worker", None),
            retries=getattr(result, "retries", None),
        )
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.get(
    "/workers/{worker_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WorkerStatsResponse,
)
def get_worker_stats(
    worker_id: str,
) -> WorkerStatsResponse:
    """
    Get Celery worker statistics for a specific worker (superuser only).
    Returns comprehensive worker stats including uptime, memory usage, and task counts.
    """
    try:
        worker_stats = get_worker_stats_by_id(worker_id=worker_id)

        if not worker_stats:
            raise HTTPException(
                status_code=404, detail=f"Worker with ID '{worker_id}' not found"
            )

        return WorkerStatsResponse(
            worker_id=worker_stats["worker_id"],
            worker_name=worker_stats["worker_name"],
            status=worker_stats["status"],
            uptime=worker_stats.get("uptime"),
            pid=worker_stats.get("pid"),
            clock=worker_stats.get("clock"),
            prefetch_count=worker_stats.get("prefetch_count"),
            pool=worker_stats.get("pool"),
            broker=worker_stats.get("broker"),
            total_tasks=worker_stats.get("total_tasks"),
            rusage=worker_stats.get("rusage"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting worker stats for {worker_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get worker stats: {str(e)}"
        )


@router.get("/workers", dependencies=[Depends(get_current_active_superuser)])
def get_worker_status() -> dict[str, Any]:
    """
    Get Celery worker status (superuser only).
    """
    try:
        i = celery_app.control.inspect()
        return {
            "active": i.active() or {},
            "scheduled": i.scheduled() or {},
            "reserved": i.reserved() or {},
            "stats": i.stats() or {},
        }
    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get worker status: {str(e)}"
        )


@router.get("/periodic-tasks", dependencies=[Depends(get_current_active_superuser)])
def get_periodic_tasks() -> list[PeriodicTaskResponse]:
    """
    Get Celery beat periodic tasks configuration (superuser only).
    """
    try:
        beat_schedule = celery_app.conf.beat_schedule
        periodic_tasks = []

        for name, task_config in beat_schedule.items():
            # Format schedule for display
            schedule = task_config.get("schedule")
            if isinstance(schedule, int | float):
                schedule_str = f"Every {schedule} seconds"
            elif hasattr(schedule, "human_readable"):
                schedule_str = schedule.human_readable
            elif str(type(schedule).__name__) == "crontab":
                # Handle celery crontab schedules
                parts = []
                if hasattr(schedule, "minute") and schedule.minute != "*":
                    parts.append(f"minute={schedule.minute}")
                if hasattr(schedule, "hour") and schedule.hour != "*":
                    parts.append(f"hour={schedule.hour}")
                if hasattr(schedule, "day_of_week") and schedule.day_of_week != "*":
                    parts.append(f"day_of_week={schedule.day_of_week}")
                if hasattr(schedule, "day_of_month") and schedule.day_of_month != "*":
                    parts.append(f"day_of_month={schedule.day_of_month}")
                if hasattr(schedule, "month_of_year") and schedule.month_of_year != "*":
                    parts.append(f"month_of_year={schedule.month_of_year}")

                if parts:
                    schedule_str = f"Crontab: {', '.join(parts)}"
                else:
                    schedule_str = "Crontab: every minute"
            else:
                schedule_str = str(schedule)

            periodic_task = PeriodicTaskResponse(
                name=name,
                task=task_config.get("task", ""),
                schedule=schedule_str,
                enabled=task_config.get("enabled", True),
                args=task_config.get("args", []),
                kwargs=task_config.get("kwargs", {}),
                # Note: last_run_at and total_run_count would require celery-beat database integration
                # For now, we'll leave these as None since we're using file-based beat schedule
                last_run_at=None,
                total_run_count=None,
            )
            periodic_tasks.append(periodic_task)

        return periodic_tasks
    except Exception as e:
        logger.error(f"Error getting periodic tasks: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get periodic tasks: {str(e)}"
        )
