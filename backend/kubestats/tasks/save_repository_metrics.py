"""
Repository metrics saving tasks for creating consolidated metrics snapshots.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from kubestats.celery_app import celery_app
from kubestats.core.db import engine
from kubestats.core.github_client import get_repository
from kubestats.models import Repository, RepositoryMetrics

logger = logging.getLogger(__name__)


def parse_datetime_field(date_str: str | None) -> datetime | None:
    """Parse a datetime string from GitHub API format."""
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def parse_github_stats(github_stats: dict[str, Any]) -> dict[str, Any]:
    """Parse GitHub stats into standardized metrics format."""
    # Handle datetime fields
    updated_at = github_stats.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = parse_datetime_field(updated_at)
    elif not isinstance(updated_at, datetime):
        updated_at = datetime.now(timezone.utc)

    pushed_at = github_stats.get("pushed_at")
    if isinstance(pushed_at, str):
        pushed_at = parse_datetime_field(pushed_at)

    return {
        "stars_count": github_stats.get(
            "stars_count", github_stats.get("stargazers_count", 0)
        ),
        "forks_count": github_stats.get("forks_count", 0),
        "watchers_count": github_stats.get("watchers_count", 0),
        "open_issues_count": github_stats.get("open_issues_count", 0),
        "size": github_stats.get("size", 0),
        "updated_at": updated_at,
        "pushed_at": pushed_at,
    }


def get_repository_by_id(session: Session, repository_id: str) -> Repository:
    """Get repository by ID with error handling."""
    repo_uuid = uuid.UUID(repository_id)
    repository = session.get(Repository, repo_uuid)
    if not repository:
        raise ValueError(f"Repository {repository_id} not found")
    return repository


def get_github_metrics(
    repository: Repository, provided_stats: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Get GitHub metrics from provided stats or API, ensuring all required fields are present."""
    required_fields = [
        "stars_count",
        "forks_count",
        "watchers_count",
        "open_issues_count",
        "size",
        "updated_at",
    ]

    if provided_stats:
        parsed_stats = parse_github_stats(provided_stats)

        # Check if any required fields are missing
        missing_fields = [
            field
            for field in required_fields
            if field not in provided_stats or provided_stats[field] is None
        ]

        if missing_fields:
            logger.warning(
                f"Missing fields {missing_fields} in provided stats, fetching from GitHub API"
            )
            try:
                github_data = get_repository(repository.owner, repository.name)
                api_stats = parse_github_stats(github_data)
                # Merge: provided stats take precedence, but fill in missing fields from API
                for field in missing_fields:
                    if field in api_stats:
                        parsed_stats[field] = api_stats[field]
            except Exception as api_error:
                logger.warning(f"Failed to fetch missing GitHub data: {api_error}")
                # Use defaults for missing fields
                for field in missing_fields:
                    if field == "updated_at":
                        parsed_stats[field] = datetime.now(timezone.utc)
                    else:
                        parsed_stats[field] = 0

        return parsed_stats

    # Fetch fresh GitHub API data
    try:
        github_data = get_repository(repository.owner, repository.name)
        return parse_github_stats(github_data)
    except Exception as github_error:
        logger.error(
            f"Failed to fetch GitHub data for {repository.full_name}: {github_error}"
        )
        return get_fallback_metrics(repository)


def get_fallback_metrics(repository: Repository) -> dict[str, Any]:
    """Get fallback metrics from previous repository metrics or defaults."""
    # Try to use previous metrics if GitHub API fails
    if hasattr(repository, "metrics") and repository.metrics:
        latest_metrics = max(repository.metrics, key=lambda m: m.recorded_at)
        return {
            "stars_count": latest_metrics.stars_count,
            "forks_count": latest_metrics.forks_count,
            "watchers_count": latest_metrics.watchers_count,
            "open_issues_count": latest_metrics.open_issues_count,
            "size": latest_metrics.size,
            "updated_at": latest_metrics.updated_at,
            "pushed_at": latest_metrics.pushed_at,
        }

    # Use defaults if no previous metrics exist
    logger.warning(
        f"No previous metrics found, using defaults for {repository.full_name}"
    )
    return {
        "stars_count": 0,
        "forks_count": 0,
        "watchers_count": 0,
        "open_issues_count": 0,
        "size": 0,
        "updated_at": datetime.now(timezone.utc),
        "pushed_at": None,
    }


def create_metrics_snapshot(
    session: Session,
    repository: Repository,
    github_metrics: dict[str, Any],
    kubernetes_resources_count: int,
) -> RepositoryMetrics:
    """Create and save a complete metrics snapshot."""
    current_time = datetime.now(timezone.utc)
    metrics_snapshot = RepositoryMetrics(
        repository_id=repository.id,
        stars_count=github_metrics["stars_count"],
        forks_count=github_metrics["forks_count"],
        watchers_count=github_metrics["watchers_count"],
        open_issues_count=github_metrics["open_issues_count"],
        size=github_metrics["size"],
        kubernetes_resources_count=kubernetes_resources_count,
        updated_at=github_metrics["updated_at"],
        pushed_at=github_metrics["pushed_at"],
        recorded_at=current_time,
    )
    session.add(metrics_snapshot)
    session.commit()
    return metrics_snapshot


@celery_app.task(bind=True)  # type: ignore[misc]
def save_repository_metrics(
    self: Any,
    repository_id: str,
    kubernetes_resources_count: int = 0,
    github_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a complete metrics snapshot for a repository.

    This task combines GitHub metrics with Kubernetes resource count to create
    a complete metrics snapshot. If github_stats are provided but incomplete,
    missing fields will be fetched from the GitHub API.

    Args:
        repository_id: UUID string of the repository to create metrics for
        kubernetes_resources_count: Number of Kubernetes resources found in the repo
        github_stats: Optional GitHub stats dict - missing fields will be fetched from API
    """
    try:
        with Session(engine) as session:
            # Get repository with error handling
            repository = get_repository_by_id(session, repository_id)

            # Get GitHub metrics (from provided stats or API, filling in missing fields)
            github_metrics = get_github_metrics(repository, github_stats)

            # Create and save metrics snapshot
            create_metrics_snapshot(
                session, repository, github_metrics, kubernetes_resources_count
            )

            result = {
                "repository_id": repository_id,
                "repository_name": repository.full_name,
                "status": "success",
                "metrics": {
                    "stars_count": github_metrics["stars_count"],
                    "forks_count": github_metrics["forks_count"],
                    "watchers_count": github_metrics["watchers_count"],
                    "open_issues_count": github_metrics["open_issues_count"],
                    "size": github_metrics["size"],
                    "kubernetes_resources_count": kubernetes_resources_count,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                },
            }
            return result

    except Exception as exc:
        logger.error(
            f"Error saving repository metrics for {repository_id}: {str(exc)}",
            exc_info=True,
        )

        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)
        self.retry(countdown=retry_in, max_retries=2, exc=exc)
        return {}  # This return is never reached but satisfies mypy
