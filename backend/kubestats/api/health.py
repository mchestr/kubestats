import datetime
import logging
from typing import Any

import redis  # type: ignore[import-untyped]
from fastapi import APIRouter
from sqlmodel import func, select

from kubestats.api.deps import SessionDep
from kubestats.core.config import settings

logger = logging.getLogger(__name__)

health_router = APIRouter()


@health_router.get("/health", summary="Check system health")
def system_health_check(session: SessionDep) -> dict[str, Any]:
    """
    Periodic task to check system health and log status.
    Returns:
        dict: System health status
    """
    start_time = datetime.datetime.now(datetime.UTC)
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        redis_status = r.ping()
        session.exec(select(func.literal(1)))
        health_data = {
            "timestamp": start_time.isoformat(),
            "redis_status": "healthy" if redis_status else "unhealthy",
            "database_status": "healthy",
            "status": "healthy",
        }
        return health_data
    except Exception as exc:
        logger.error(f"System health check failed: {str(exc)}")
        return {
            "timestamp": start_time.isoformat(),
            "status": "unhealthy",
            "error": str(exc),
        }
