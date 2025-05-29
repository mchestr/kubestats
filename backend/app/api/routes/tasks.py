import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.api.deps import SessionDep, get_current_active_superuser
from app.celery_app import celery_app
from app.crud import get_task_status_from_db
from app.models import User
from app.tasks.basic_tasks import create_log_entry, system_health_check

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
    "/list",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[TaskStatusResponse],
)
def list_tasks(
    session: SessionDep,
) -> list[TaskStatusResponse]:
    """
    List recent tasks (superuser only).
    """
    try:
        tasks = get_task_status_from_db(db=session)

        return [
            TaskStatusResponse(
                task_id=task["task_id"],
                status=task["status"],
                result=task["result"],
                traceback=task["traceback"],
                date_done=task["date_done"],
                name=task["name"],
                worker=task["worker"],
                retries=task["retries"],
            )
            for task in tasks
        ]
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


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
