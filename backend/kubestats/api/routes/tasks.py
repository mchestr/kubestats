import json
import logging
import pickle
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlmodel import Session, desc, select

from kubestats.api.deps import get_current_active_superuser, get_db
from kubestats.celery_app import celery_app
from kubestats.models import CeleryTaskMeta, User

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
        """Convert exception objects to string representation and decode all result formats."""
        if isinstance(v, Exception):
            return f"{type(v).__name__}: {str(v)}"
        return decode_and_parse_result(v)


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


class TaskMetaResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None
    date_done: str | None = None
    traceback: str | None = None
    name: str | None = None
    args: str | None = None
    kwargs: str | None = None
    worker: str | None = None
    retries: int | None = None

    @field_validator("result", mode="before")
    @classmethod
    def parse_json_result(cls, v: Any) -> Any:
        """Decode and parse all result formats including pickled data and JSON."""
        return decode_and_parse_result(v)

    @field_validator("args", "kwargs", "traceback", mode="before")
    @classmethod
    def decode_string_fields(cls, v: Any) -> str | None:
        """Decode string fields that might contain pickled data or memoryview objects."""
        return decode_string_field(v)


def decode_and_parse_result(val: Any) -> Any:
    """
    Comprehensive decoder for Celery task results that handles:
    - Memoryview objects (convert to bytes)
    - Pickled binary data (unpickle safely)
    - JSON strings (parse to objects)
    - Regular strings and other types (return as-is)
    """
    # Handle memoryview objects first
    if isinstance(val, memoryview):
        try:
            val = val.tobytes()
        except Exception:
            return str(val)

    # Try unpickling if it's bytes (likely legacy pickled data)
    if isinstance(val, bytes):
        try:
            # Attempt to unpickle - this handles legacy Celery data
            return pickle.loads(val)
        except Exception:
            # If unpickling fails, try decoding as UTF-8
            try:
                val = val.decode("utf-8", errors="replace")
            except Exception:
                return str(val)

    # Try JSON parsing if it's a string that looks like JSON
    if isinstance(val, str):
        # Skip empty or whitespace-only strings
        if not val.strip():
            return val

        # Try to parse as JSON if it looks like structured data
        stripped = val.strip()
        if stripped.startswith(("{", "[", '"')) or stripped in (
            "true",
            "false",
            "null",
        ):
            try:
                return json.loads(val)
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, return the string as-is
                pass

    return val


def decode_string_field(val: Any) -> str | None:
    """
    Decode string fields that might contain pickled data or memoryview objects.
    Always returns a string or None to maintain type compatibility.
    """
    if val is None:
        return None

    # Handle memoryview objects first
    if isinstance(val, memoryview):
        try:
            val = val.tobytes()
        except Exception:
            return str(val)

    # Try unpickling if it's bytes, but convert result to string
    if isinstance(val, bytes):
        try:
            # Attempt to unpickle
            unpickled = pickle.loads(val)
            # Convert the result to a string representation
            return str(unpickled) if unpickled is not None else None
        except Exception:
            # If unpickling fails, try decoding as UTF-8
            try:
                return val.decode("utf-8", errors="replace")
            except Exception:
                return str(val)

    # Return as string
    return str(val) if val is not None else None


def decode_if_memoryview(val: Any) -> Any:
    """Legacy function - use decode_and_parse_result for result fields."""
    return decode_and_parse_result(val)


def parse_json_if_string(val: Any) -> Any:
    """Legacy function - use decode_and_parse_result instead."""
    return decode_and_parse_result(val)


def ensure_utc_isoformat(dt: datetime | None) -> str | None:
    """
    Ensure the datetime is returned as an ISO8601 string with UTC timezone info.
    If dt is naive, assume UTC. If None, return None.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


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
                detail=f"Periodic task '{task_name}' not found in schedule",
            )

        # Get task details
        task_func = task_config.get("task", "")
        task_args = task_config.get("args", [])
        task_kwargs = task_config.get("kwargs", {})

        # Trigger the task
        result = celery_app.send_task(task_func, args=task_args, kwargs=task_kwargs)

        logger.info(
            f"Periodic task '{task_name}' triggered by user {current_user.id}: {result.id}"
        )

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
            detail=f"Failed to trigger periodic task '{task_name}': {str(e)}",
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
            date_done=ensure_utc_isoformat(result.date_done),
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
    "/workers",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=WorkerStatusResponse,
)
def get_worker_status() -> WorkerStatusResponse:
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


@router.get(
    "/tasks/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[TaskMetaResponse],
)
def list_tasks(
    status: str | None = Query(
        None, description="Filter by task status (e.g., PENDING, FAILURE, SUCCESS)"
    ),
    since: datetime | None = Query(
        None, description="Only tasks after this datetime (ISO8601)"
    ),
    until: datetime | None = Query(
        None, description="Only tasks before this datetime (ISO8601)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Max number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: Session = Depends(get_db),
) -> list[TaskMetaResponse]:
    """
    List Celery task metadata with optional filtering by status and time period (superuser only).
    """
    query = select(CeleryTaskMeta)
    if status:
        query = query.where(CeleryTaskMeta.status == status)
    if since:
        query = query.where(CeleryTaskMeta.date_done >= since)
    if until:
        query = query.where(CeleryTaskMeta.date_done <= until)
    query = query.order_by(desc(CeleryTaskMeta.date_done)).offset(offset).limit(limit)
    results = session.exec(query).all()
    return [
        TaskMetaResponse(
            task_id=task.task_id,
            status=task.status,
            result=task.result,
            date_done=ensure_utc_isoformat(task.date_done),
            traceback=task.traceback,
            name=task.name,
            args=task.args,
            kwargs=task.kwargs,
            worker=task.worker,
            retries=task.retries,
        )
        for task in results
    ]
