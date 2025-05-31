import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlmodel import Session

from kubestats.api.deps import get_current_active_superuser, get_db
from kubestats.celery_app import celery_app
from kubestats.core.config import settings
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
    total_run_count: int | None = None
    args: list[Any] | None = None
    kwargs: dict[str, Any] | None = None


class WorkerStatusResponse(BaseModel):
    active: dict[str, Any]
    scheduled: dict[str, Any]
    reserved: dict[str, Any]
    stats: dict[str, Any]
    periodic_tasks: list[PeriodicTaskResponse]


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


@router.post("/trigger-periodic/{task_name}", response_model=TaskResponse)
def trigger_periodic_task(
    task_name: str,
    current_user: User = Depends(get_current_active_superuser),
) -> TaskResponse:
    """
    Trigger a periodic task by name (superuser only).
    """
    try:
        # Get the beat schedule configuration
        beat_schedule = celery_app.conf.beat_schedule
        
        # Find the task configuration
        task_config = None
        for schedule_name, config in beat_schedule.items():
            if schedule_name == task_name:
                task_config = config
                break
        
        if not task_config:
            raise HTTPException(
                status_code=404, 
                detail=f"Periodic task '{task_name}' not found in schedule"
            )
        
        # Get task details
        task_func = task_config.get("task", "")
        task_args = task_config.get("args", [])
        task_kwargs = task_config.get("kwargs", {})
        
        # Trigger the task
        result = celery_app.send_task(
            task_func,
            args=task_args,
            kwargs=task_kwargs
        )

        logger.info(f"Periodic task '{task_name}' triggered by user {current_user.id}: {result.id}")

        return TaskResponse(
            task_id=result.id,
            status="PENDING",
            message=f"Periodic task '{task_name}' triggered successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering periodic task '{task_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to trigger periodic task '{task_name}': {str(e)}"
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


@router.get("/workers", dependencies=[Depends(get_current_active_superuser)], response_model=WorkerStatusResponse)
def get_worker_status(
    session: Session = Depends(get_db),
) -> WorkerStatusResponse:
    """
    Get Celery worker status and periodic tasks configuration (superuser only).
    """
    try:
        inspector = celery_app.control.inspect()
        worker_data = {
            "active": inspector.active() or {},
            "scheduled": inspector.scheduled() or {},
            "reserved": inspector.reserved() or {},
            "stats": inspector.stats() or {},
        }
        
        # Get periodic tasks from the beat_schedule configuration
        periodic_tasks = []
        beat_schedule = celery_app.conf.beat_schedule
        
        # Aggregate task stats across all workers for periodic tasks
        task_stats = {}
        for _, stats in worker_data["stats"].items():
            if "total" in stats:
                for task_name, count in stats["total"].items():
                    if task_name not in task_stats:
                        task_stats[task_name] = 0
                    task_stats[task_name] += count
        
        for name, task_config in beat_schedule.items():
            task_name = task_config.get("task", "")
            total_run_count = task_stats.get(task_name, 0)
            
            periodic_task = PeriodicTaskResponse(
                name=name,
                task=task_name,
                schedule=str(task_config.get("schedule")),
                enabled=task_config.get("enabled", True),
                args=task_config.get("args", []),
                kwargs=task_config.get("kwargs", {}),
                total_run_count=total_run_count if total_run_count > 0 else None,
            )
            periodic_tasks.append(periodic_task)
        
        return WorkerStatusResponse(
            active=worker_data["active"],
            scheduled=worker_data["scheduled"],
            reserved=worker_data["reserved"],
            stats=worker_data["stats"],
            periodic_tasks=periodic_tasks,
        )
    except Exception as e:
        logger.error(f"Error getting worker status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get worker status: {str(e)}"
        )
