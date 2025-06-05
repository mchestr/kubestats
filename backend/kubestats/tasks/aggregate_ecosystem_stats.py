"""
Daily ecosystem statistics aggregation task.
"""

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Any

from sqlmodel import Session, desc, func, select

from kubestats.celery_app import celery_app
from kubestats.core.db import engine
from kubestats.models import (
    EcosystemStats,
    KubernetesResource,
    KubernetesResourceEvent,
    Repository,
    RepositoryMetrics,
)

log = logging.getLogger(__name__)


def get_start_of_day(date: datetime) -> datetime:
    """Get the start of day for a given date in UTC"""
    return datetime.combine(date.date(), time.min, timezone.utc)


def calculate_repository_stats(session: Session) -> dict[str, Any]:
    """Calculate repository-related statistics"""
    log.info("Calculating repository statistics")

    # Total repositories
    total_repos = session.exec(select(func.count()).select_from(Repository)).one()

    # Repositories with resources
    repos_with_resources = session.exec(
        select(func.count(func.distinct(KubernetesResource.repository_id))).where(
            KubernetesResource.status == "ACTIVE"
        )
    ).one()

    # Language breakdown
    language_query = select(Repository.language, func.count()).group_by(
        Repository.language
    )
    languages = session.exec(language_query).all()
    language_breakdown = {
        lang or "Unknown": count for lang, count in languages if count > 0
    }

    # Topic breakdown (flatten topics from all repositories)
    topic_counts: dict[str, int] = {}
    topic_query = select(Repository.topics)
    for topics in session.exec(topic_query):
        if topics:
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Get top 20 topics
    popular_topics = dict(
        sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    )

    return {
        "total_repositories": total_repos,
        "repositories_with_resources": repos_with_resources,
        "language_breakdown": language_breakdown,
        "popular_topics": popular_topics,
    }


def calculate_resource_stats(session: Session) -> dict[str, Any]:
    """Calculate Kubernetes resource-related statistics"""
    log.info("Calculating resource statistics")

    # Total and active resources
    total_resources = session.exec(
        select(func.count()).select_from(KubernetesResource)
    ).one()
    active_resources = session.exec(
        select(func.count())
        .select_from(KubernetesResource)
        .where(KubernetesResource.status == "ACTIVE")
    ).one()

    # Resource type breakdown
    resource_type_query = (
        select(KubernetesResource.kind, func.count())
        .where(KubernetesResource.status == "ACTIVE")
        .group_by(KubernetesResource.kind)
    )

    resource_types = session.exec(resource_type_query).all()
    resource_type_breakdown = dict(resource_types)

    # Popular Helm releases (use HelmRelease names)
    helm_release_counts: dict[str, int] = {}
    helm_releases = session.exec(
        select(KubernetesResource.name).where(
            KubernetesResource.kind == "HelmRelease",
            KubernetesResource.status == "ACTIVE",
        )
    ).all()

    for release_name in helm_releases:
        if release_name:
            helm_release_counts[release_name] = (
                helm_release_counts.get(release_name, 0) + 1
            )

    # Get top 20 helm releases
    popular_helm_charts = dict(
        sorted(helm_release_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    )

    # Total events
    total_events = session.exec(
        select(func.count()).select_from(KubernetesResourceEvent)
    ).one()

    return {
        "total_resources": total_resources,
        "active_resources": active_resources,
        "resource_type_breakdown": resource_type_breakdown,
        "popular_helm_charts": popular_helm_charts,
        "total_resource_events": total_events,
    }


def calculate_daily_activity(session: Session, target_date: datetime) -> dict[str, Any]:
    """Calculate daily activity for the target date"""
    log.info(f"Calculating daily activity for {target_date.date()}")

    start_of_day = get_start_of_day(target_date)
    end_of_day = start_of_day.replace(hour=23, minute=59, second=59)

    # Daily resource events
    created_count = session.exec(
        select(func.count())
        .select_from(KubernetesResourceEvent)
        .where(
            KubernetesResourceEvent.event_type == "CREATED",
            KubernetesResourceEvent.event_timestamp >= start_of_day,
            KubernetesResourceEvent.event_timestamp <= end_of_day,
        )
    ).one()

    modified_count = session.exec(
        select(func.count())
        .select_from(KubernetesResourceEvent)
        .where(
            KubernetesResourceEvent.event_type == "MODIFIED",
            KubernetesResourceEvent.event_timestamp >= start_of_day,
            KubernetesResourceEvent.event_timestamp <= end_of_day,
        )
    ).one()

    deleted_count = session.exec(
        select(func.count())
        .select_from(KubernetesResourceEvent)
        .where(
            KubernetesResourceEvent.event_type == "DELETED",
            KubernetesResourceEvent.event_timestamp >= start_of_day,
            KubernetesResourceEvent.event_timestamp <= end_of_day,
        )
    ).one()

    return {
        "daily_created_resources": created_count,
        "daily_modified_resources": modified_count,
        "daily_deleted_resources": deleted_count,
    }


def calculate_metrics_aggregates(session: Session) -> dict[str, Any]:
    """Calculate aggregated repository metrics"""
    log.info("Calculating repository metrics aggregates")

    # Get all repository IDs first
    repo_ids_query = select(RepositoryMetrics.repository_id).distinct()
    repo_ids = list(session.exec(repo_ids_query).all())

    total_stars = 0
    total_forks = 0
    total_watchers = 0
    total_open_issues = 0

    # For each repository, get the latest metrics
    for repo_id in repo_ids:
        latest_metric_query = (
            select(RepositoryMetrics)
            .where(RepositoryMetrics.repository_id == repo_id)
            .order_by(desc(RepositoryMetrics.recorded_at))
            .limit(1)
        )
        latest_metric = session.exec(latest_metric_query).first()
        if latest_metric:
            total_stars += latest_metric.stars_count
            total_forks += latest_metric.forks_count
            total_watchers += latest_metric.watchers_count
            total_open_issues += latest_metric.open_issues_count

    return {
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_watchers": total_watchers,
        "total_open_issues": total_open_issues,
    }


def calculate_growth_metrics(
    session: Session, current_stats: dict[str, Any], target_date: datetime
) -> dict[str, Any]:
    """Calculate growth metrics compared to previous day"""
    log.info("Calculating growth metrics")

    previous_date = target_date - timedelta(days=1)

    # Try to get previous day's stats
    previous_stats = session.exec(
        select(EcosystemStats).where(
            func.date(EcosystemStats.date) == previous_date.date()
        )
    ).first()

    if previous_stats:
        repository_growth = (
            current_stats["total_repositories"] - previous_stats.total_repositories
        )
        resource_growth = (
            current_stats["active_resources"] - previous_stats.active_resources
        )
        star_growth = current_stats["total_stars"] - previous_stats.total_stars
    else:
        # No previous data, so no growth to calculate
        repository_growth = 0
        resource_growth = 0
        star_growth = 0

    return {
        "repository_growth": repository_growth,
        "resource_growth": resource_growth,
        "star_growth": star_growth,
    }


def set_ecosystem_stats_fields(
    stats_obj: EcosystemStats,
    combined_stats: dict[str, Any],
    calculation_duration: float,
    activity_date: datetime | None = None,
) -> EcosystemStats:
    if activity_date is not None:
        stats_obj.date = activity_date
    stats_obj.total_repositories = combined_stats["total_repositories"]
    stats_obj.active_repositories = combined_stats[
        "total_repositories"
    ]  # For now, assume all are active
    stats_obj.repositories_with_resources = combined_stats[
        "repositories_with_resources"
    ]
    stats_obj.total_resources = combined_stats["total_resources"]
    stats_obj.active_resources = combined_stats["active_resources"]
    stats_obj.total_resource_events = combined_stats["total_resource_events"]
    stats_obj.resource_type_breakdown = combined_stats["resource_type_breakdown"]
    stats_obj.popular_helm_charts = combined_stats["popular_helm_charts"]
    stats_obj.daily_created_resources = combined_stats["daily_created_resources"]
    stats_obj.daily_modified_resources = combined_stats["daily_modified_resources"]
    stats_obj.daily_deleted_resources = combined_stats["daily_deleted_resources"]
    stats_obj.total_stars = combined_stats["total_stars"]
    stats_obj.total_forks = combined_stats["total_forks"]
    stats_obj.total_watchers = combined_stats["total_watchers"]
    stats_obj.total_open_issues = combined_stats["total_open_issues"]
    stats_obj.language_breakdown = combined_stats["language_breakdown"]
    stats_obj.popular_topics = combined_stats["popular_topics"]
    stats_obj.repository_growth = combined_stats["repository_growth"]
    stats_obj.resource_growth = combined_stats["resource_growth"]
    stats_obj.star_growth = combined_stats["star_growth"]
    stats_obj.calculation_duration_seconds = calculation_duration
    return stats_obj


@celery_app.task(bind=True)  # type: ignore[misc]
def aggregate_daily_ecosystem_stats(
    self: Any, target_date: str | None = None
) -> dict[str, Any]:
    """
    Aggregate daily ecosystem statistics for trend analysis.

    This task calculates and stores a comprehensive snapshot of the Kubernetes
    ecosystem including repository metrics, resource statistics, and activity trends.

    Args:
        target_date: Optional date string (YYYY-MM-DD). If not provided, uses current date.

    Returns:
        Dictionary containing aggregation results and summary
    """
    start_time = datetime.now(timezone.utc)
    try:
        with Session(engine) as session:
            # Parse target date or use current date
            if target_date:
                try:
                    activity_date = datetime.fromisoformat(target_date)
                    if activity_date.tzinfo is None:
                        activity_date = activity_date.replace(tzinfo=timezone.utc)
                except Exception as e:
                    log.error(f"Invalid date format: {target_date}")
                    raise ValueError("Invalid date format") from e
            else:
                activity_date = start_time - timedelta(days=1)
            # Calculate daily activity for the previous day to get complete data

            log.info(f"Starting ecosystem stats aggregation for {activity_date.date()}")

            # Check if stats already exist for this date
            existing_stats = session.exec(
                select(EcosystemStats).where(
                    func.date(EcosystemStats.date) == activity_date.date()
                )
            ).first()

            # Calculate all statistics
            repo_stats = calculate_repository_stats(session)
            resource_stats = calculate_resource_stats(session)
            daily_activity = calculate_daily_activity(session, activity_date)
            metrics_aggregates = calculate_metrics_aggregates(session)

            # Combine all stats
            combined_stats = {
                **repo_stats,
                **resource_stats,
                **daily_activity,
                **metrics_aggregates,
            }

            # Calculate growth metrics
            growth_metrics = calculate_growth_metrics(
                session, combined_stats, activity_date
            )
            combined_stats.update(growth_metrics)

            # Calculate execution time
            calculation_duration = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()

            if existing_stats:
                log.info(f"Stats already exist for {activity_date.date()}, updating")
                set_ecosystem_stats_fields(
                    existing_stats, combined_stats, calculation_duration
                )
                session.add(existing_stats)
                session.commit()
                log.info(
                    f"Successfully updated ecosystem stats for {activity_date.date()}. "
                    f"Duration: {calculation_duration:.2f}s"
                )
            else:
                ecosystem_stats = EcosystemStats()
                set_ecosystem_stats_fields(
                    ecosystem_stats, combined_stats, calculation_duration, activity_date
                )
                session.add(ecosystem_stats)
                session.commit()
                log.info(
                    f"Successfully aggregated ecosystem stats for {activity_date.date()}. "
                    f"Duration: {calculation_duration:.2f}s"
                )
            return {
                "status": "updated" if existing_stats else "success",
                "date": activity_date.isoformat(),
                "stats": {
                    "total_repositories": combined_stats["total_repositories"],
                    "total_resources": combined_stats["total_resources"],
                    "active_resources": combined_stats["active_resources"],
                    "daily_activity": {
                        "created": combined_stats["daily_created_resources"],
                        "modified": combined_stats["daily_modified_resources"],
                        "deleted": combined_stats["daily_deleted_resources"],
                    },
                    "growth": {
                        "repositories": combined_stats["repository_growth"],
                        "resources": combined_stats["resource_growth"],
                        "stars": combined_stats["star_growth"],
                    },
                },
                "calculation_duration_seconds": calculation_duration,
            }
    except Exception as exc:
        log.error(
            f"Error aggregating ecosystem stats for {target_date if target_date else 'yesterday'}: {str(exc)}",
            exc_info=True,
        )

        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)
        self.retry(countdown=retry_in, max_retries=2, exc=exc)
        return {}  # This return is never reached but satisfies mypy
