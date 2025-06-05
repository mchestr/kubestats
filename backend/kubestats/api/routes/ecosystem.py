"""
API endpoints for ecosystem statistics and trends.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import asc, desc, func, select

from kubestats.api.deps import SessionDep, get_current_active_superuser
from kubestats.models import (
    EcosystemStats,
    EcosystemStatsListPublic,
    EcosystemStatsPublic,
    EcosystemTrendPublic,
    EcosystemTrendsPublic,
    HelmReleaseActivityListPublic,
    HelmReleaseActivityPublic,
    HelmReleaseChangePublic,
    KubernetesResourceEvent,
)

router = APIRouter()


@router.get("/", response_model=EcosystemStatsListPublic)
def get_ecosystem_stats(
    session: SessionDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
) -> Any:
    """
    Get historical ecosystem statistics.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        days: Number of days of data to return (from today backwards)
    """
    # Calculate date range
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)

    # Query ecosystem stats
    count_stmt = (
        select(func.count())
        .select_from(EcosystemStats)
        .where(
            func.date(EcosystemStats.date) >= start_date,
            func.date(EcosystemStats.date) <= end_date,
        )
    )
    count = session.exec(count_stmt).one()

    stats_stmt = (
        select(EcosystemStats)
        .where(
            func.date(EcosystemStats.date) >= start_date,
            func.date(EcosystemStats.date) <= end_date,
        )
        .order_by(desc(EcosystemStats.date))
        .offset(skip)
        .limit(limit)
    )

    stats = session.exec(stats_stmt).all()

    # Convert to public models
    stats_public = [
        EcosystemStatsPublic(
            id=stat.id,
            date=stat.date,
            total_repositories=stat.total_repositories,
            active_repositories=stat.active_repositories,
            repositories_with_resources=stat.repositories_with_resources,
            total_resources=stat.total_resources,
            active_resources=stat.active_resources,
            total_resource_events=stat.total_resource_events,
            resource_type_breakdown=stat.resource_type_breakdown,
            popular_helm_charts=stat.popular_helm_charts,
            daily_created_resources=stat.daily_created_resources,
            daily_modified_resources=stat.daily_modified_resources,
            daily_deleted_resources=stat.daily_deleted_resources,
            total_stars=stat.total_stars,
            total_forks=stat.total_forks,
            total_watchers=stat.total_watchers,
            total_open_issues=stat.total_open_issues,
            language_breakdown=stat.language_breakdown,
            popular_topics=stat.popular_topics,
            repository_growth=stat.repository_growth,
            resource_growth=stat.resource_growth,
            star_growth=stat.star_growth,
            calculated_at=stat.calculated_at,
            calculation_duration_seconds=stat.calculation_duration_seconds,
        )
        for stat in stats
    ]

    return EcosystemStatsListPublic(data=stats_public, count=count)


@router.get("/latest", response_model=EcosystemStatsPublic)
def get_latest_ecosystem_stats(session: SessionDep) -> Any:
    """Get the most recent ecosystem statistics."""
    stmt = select(EcosystemStats).order_by(desc(EcosystemStats.date)).limit(1)
    latest_stat = session.exec(stmt).first()

    if not latest_stat:
        raise HTTPException(status_code=404, detail="No ecosystem statistics found")

    return EcosystemStatsPublic(
        id=latest_stat.id,
        date=latest_stat.date,
        total_repositories=latest_stat.total_repositories,
        active_repositories=latest_stat.active_repositories,
        repositories_with_resources=latest_stat.repositories_with_resources,
        total_resources=latest_stat.total_resources,
        active_resources=latest_stat.active_resources,
        total_resource_events=latest_stat.total_resource_events,
        resource_type_breakdown=latest_stat.resource_type_breakdown,
        popular_helm_charts=latest_stat.popular_helm_charts,
        daily_created_resources=latest_stat.daily_created_resources,
        daily_modified_resources=latest_stat.daily_modified_resources,
        daily_deleted_resources=latest_stat.daily_deleted_resources,
        total_stars=latest_stat.total_stars,
        total_forks=latest_stat.total_forks,
        total_watchers=latest_stat.total_watchers,
        total_open_issues=latest_stat.total_open_issues,
        language_breakdown=latest_stat.language_breakdown,
        popular_topics=latest_stat.popular_topics,
        repository_growth=latest_stat.repository_growth,
        resource_growth=latest_stat.resource_growth,
        star_growth=latest_stat.star_growth,
        calculated_at=latest_stat.calculated_at,
        calculation_duration_seconds=latest_stat.calculation_duration_seconds,
    )


@router.get("/trends", response_model=EcosystemTrendsPublic)
def get_ecosystem_trends(
    session: SessionDep,
    days: int = Query(default=30, ge=7, le=365),
) -> Any:
    """
    Get ecosystem trend data for visualization.

    Args:
        days: Number of days of trend data to return
    """
    # Calculate date range
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days)

    # Query ecosystem stats for the date range
    stmt = (
        select(EcosystemStats)
        .where(
            func.date(EcosystemStats.date) >= start_date,
            func.date(EcosystemStats.date) <= end_date,
        )
        .order_by(asc(EcosystemStats.date))
    )

    stats = session.exec(stmt).all()

    if not stats:
        raise HTTPException(
            status_code=404,
            detail="No ecosystem statistics found for the specified date range",
        )

    # Build trend data
    repository_trends = [
        EcosystemTrendPublic(
            date=stat.date.strftime("%Y-%m-%d"),
            value=stat.total_repositories,
        )
        for stat in stats
    ]

    resource_trends = [
        EcosystemTrendPublic(
            date=stat.date.strftime("%Y-%m-%d"),
            value=stat.active_resources,
        )
        for stat in stats
    ]

    activity_trends = [
        EcosystemTrendPublic(
            date=stat.date.strftime("%Y-%m-%d"),
            value=stat.daily_created_resources + stat.daily_modified_resources,
        )
        for stat in stats
    ]

    return EcosystemTrendsPublic(
        repository_trends=repository_trends,
        resource_trends=resource_trends,
        activity_trends=activity_trends,
    )


@router.post(
    "/trigger-aggregation",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=dict[str, Any],
)
def trigger_ecosystem_aggregation(
    target_date: str | None = Query(default=None),
) -> Any:
    """
    Manually trigger ecosystem statistics aggregation (superuser only).

    Args:
        target_date: Optional date string (YYYY-MM-DD). If not provided, uses current date.
    """
    from kubestats.tasks.aggregate_ecosystem_stats import (
        aggregate_daily_ecosystem_stats,
    )

    try:
        # Trigger the task
        if target_date:
            result = aggregate_daily_ecosystem_stats.delay(target_date)
        else:
            result = aggregate_daily_ecosystem_stats.delay()

        return {
            "status": "success",
            "message": "Ecosystem aggregation task triggered successfully",
            "task_id": result.id,
            "target_date": target_date or "current date",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger ecosystem aggregation: {str(e)}",
        )


@router.get("/helm-release-activity", response_model=HelmReleaseActivityListPublic)
def get_helm_release_activity(
    session: SessionDep,
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    page_size: int = Query(
        default=10, ge=1, le=50, description="Number of releases per page"
    ),
) -> dict[str, Any]:
    """
    Get the most recent HelmRelease changes (created/modified/deleted), grouped by release name.
    Returns the latest N releases with their change events and YAML, sorted by highest count.
    """
    # Query the most recent HelmRelease events
    stmt = (
        select(KubernetesResourceEvent)
        .where(KubernetesResourceEvent.resource_kind == "HelmRelease")
        .order_by(desc(KubernetesResourceEvent.event_timestamp))
        .limit(2000)  # Fetch more to allow grouping and sorting
    )
    events = session.exec(stmt).all()

    # Group by release name
    grouped: dict[str, list[KubernetesResourceEvent]] = {}
    for event in events:
        name = event.resource_name
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(event)

    # Sort grouped items by number of events (descending)
    sorted_grouped = sorted(
        grouped.items(), key=lambda item: len(item[1]), reverse=True
    )

    # Pagination
    total_releases = len(sorted_grouped)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_grouped = sorted_grouped[start:end]

    # Prepare response
    result = []
    for name, changes in paginated_grouped:
        result.append(
            HelmReleaseActivityPublic(
                release_name=name,
                changes=[
                    HelmReleaseChangePublic(
                        change_type=e.event_type,
                        timestamp=e.event_timestamp,
                        yaml=yaml.safe_dump(e.resource_data)
                        if e.resource_data
                        else None,
                        user=e.repository.full_name,  # Add user if available in your model
                    )
                    for e in changes
                ],
            )
        )

    return {"data": result, "count": total_releases}
