from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import func, select

from kubestats.api.deps import SessionDep, get_current_active_superuser
from kubestats.models import (
    KubernetesResource,
    KubernetesResourceEvent,
    Repository,
    RepositoryMetrics,
)

router = APIRouter()


class DatabaseStatsPublic:
    """Database statistics response model"""

    def __init__(
        self,
        table_counts: dict[str, int],
        sync_run_stats: dict[str, Any],
        total_records: int,
    ):
        self.table_counts = table_counts
        self.sync_run_stats = sync_run_stats
        self.total_records = total_records


@router.get(
    "/database-stats",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=dict[str, Any],
)
def get_database_stats(session: SessionDep) -> Any:
    """
    Get database table counts and sync run statistics.
    Only accessible by superusers.
    """

    # Get table counts
    repositories_count = session.exec(
        select(func.count()).select_from(Repository)
    ).one()
    repository_metrics_count = session.exec(
        select(func.count()).select_from(RepositoryMetrics)
    ).one()
    kubernetes_resources_count = session.exec(
        select(func.count()).select_from(KubernetesResource)
    ).one()
    kubernetes_events_count = session.exec(
        select(func.count()).select_from(KubernetesResourceEvent)
    ).one()

    # Get new repositories discovered in the last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_repositories_count = session.exec(
        select(func.count())
        .select_from(Repository)
        .where(Repository.discovered_at >= seven_days_ago)
    ).one()

    # Get resource changes in the last 7 days
    resource_changes_count = session.exec(
        select(func.count())
        .select_from(KubernetesResourceEvent)
        .where(KubernetesResourceEvent.event_timestamp >= seven_days_ago)
    ).one()

    # Get sync run statistics with repository names
    sync_runs_query = (
        select(  # type: ignore[call-overload]
            KubernetesResourceEvent.sync_run_id,
            func.count().label("event_count"),
            func.min(KubernetesResourceEvent.event_timestamp).label("started_at"),
            func.max(KubernetesResourceEvent.event_timestamp).label("completed_at"),
            Repository.name.label("repository_name"),  # type: ignore[attr-defined]
            Repository.full_name.label("repository_full_name"),  # type: ignore[attr-defined]
        )
        .join(Repository, KubernetesResourceEvent.repository_id == Repository.id)
        .group_by(
            KubernetesResourceEvent.sync_run_id,
            Repository.name,
            Repository.full_name,
        )
        .order_by(func.max(KubernetesResourceEvent.event_timestamp).desc())
        .limit(10)
    )

    sync_runs_data = session.exec(sync_runs_query).all()

    # Get total unique sync runs
    total_sync_runs = session.exec(
        select(
            func.count(func.distinct(KubernetesResourceEvent.sync_run_id))
        ).select_from(KubernetesResourceEvent)
    ).one()

    # Get event type breakdown for recent sync runs
    event_types_query = select(
        KubernetesResourceEvent.event_type,
        func.count().label("count"),
    ).group_by(KubernetesResourceEvent.event_type)

    event_types_data = session.exec(event_types_query).all()

    # Calculate total records across all tables
    total_records = (
        repositories_count
        + repository_metrics_count
        + kubernetes_resources_count
        + kubernetes_events_count
    )

    return {
        "table_counts": {
            "repositories": repositories_count,
            "repository_metrics": repository_metrics_count,
            "kubernetes_resources": kubernetes_resources_count,
            "kubernetes_resource_events": kubernetes_events_count,
        },
        "recent_stats": {
            "new_repositories_last_7_days": new_repositories_count,
            "resource_changes_last_7_days": resource_changes_count,
        },
        "sync_run_stats": {
            "total_sync_runs": total_sync_runs,
            "recent_sync_runs": [
                {
                    "repository_name": run[4],  # repository_name
                    "repository_full_name": run[5],  # repository_full_name
                    "event_count": run[1],  # event_count
                    "started_at": run[2].isoformat() if run[2] else None,  # started_at
                    "completed_at": (
                        run[3].isoformat() if run[3] else None
                    ),  # completed_at
                    "duration_milliseconds": (
                        (run[3] - run[2]).total_seconds() * 1000
                        if run[2] and run[3]
                        else None
                    ),
                }
                for run in sync_runs_data
            ],
            "event_type_breakdown": {
                event_type[0]: event_type[1]  # event_type, count
                for event_type in event_types_data
            },
        },
        "total_records": total_records,
    }
