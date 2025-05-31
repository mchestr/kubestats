"""
Repository scanning tasks for analyzing Kubernetes resources in Git repositories.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session

from kubestats.celery_app import celery_app
from kubestats.core.db import engine
from kubestats.core.yaml_scanner import YAMLScanner
from kubestats.models import Repository, SyncStatus
from kubestats.tasks.save_repository_metrics import save_repository_metrics

logger = logging.getLogger(__name__)


def update_scan_status(
    session: Session,
    repository: Repository,
    status: SyncStatus,
    error: str | None = None,
) -> None:
    """Update repository scan status."""
    repository.scan_status = status
    repository.scan_error = error[:2000] if error else None
    if status == SyncStatus.SUCCESS:
        repository.last_scan_at = datetime.now(timezone.utc)
    session.add(repository)
    session.commit()


def get_repository_by_id(session: Session, repository_id: str) -> Repository:
    """Get repository by ID with error handling."""
    repo_uuid = uuid.UUID(repository_id)
    repository = session.get(Repository, repo_uuid)
    if not repository:
        raise ValueError(f"Repository {repository_id} not found")
    return repository


def validate_working_directory(repository: Repository) -> Path:
    """Validate and return the working directory path for scanning."""
    if not repository.working_directory_path:
        raise ValueError(f"Repository {repository.full_name} has no working directory")

    repo_workdir = Path(repository.working_directory_path)
    if not repo_workdir.exists():
        raise ValueError(f"Working directory {repo_workdir} does not exist")

    return repo_workdir


def perform_yaml_scan(
    session: Session, repository: Repository, repo_workdir: Path
) -> Any:
    """Perform YAML scanning on the repository."""
    logger.info(f"Starting YAML scanning for repository {repository.full_name}")
    scanner = YAMLScanner(session)
    scan_result = scanner.scan_repository(repository, repo_workdir)

    logger.info(
        f"Scanned repository {repository.full_name}: "
        f"{scan_result.created_count} created, "
        f"{scan_result.modified_count} modified, "
        f"{scan_result.deleted_count} deleted, "
        f"{scan_result.total_resources} total resources"
    )
    return scan_result


def trigger_metrics_task(
    repository: Repository, scan_result: Any, github_stats: dict[str, Any] | None
) -> None:
    """Trigger the metrics saving task."""

    metrics_task = save_repository_metrics.delay(
        str(repository.id), scan_result.total_resources, github_stats
    )
    logger.info(
        f"Metrics saving task {metrics_task.id} triggered for repository {repository.full_name}"
    )


def handle_scan_error(
    repository_id: str, error: Exception, task_self: Any
) -> dict[str, Any]:
    """Handle scan errors with proper logging and status updates."""
    logger.error(
        f"Error scanning repository {repository_id}: {str(error)}", exc_info=True
    )

    try:
        repo_uuid = uuid.UUID(repository_id)
        with Session(engine) as session:
            repository = session.get(Repository, repo_uuid)
            if repository:
                update_scan_status(session, repository, SyncStatus.ERROR, str(error))
    except Exception as update_error:
        logger.error(
            f"Failed to update error status for repository {repository_id}: {str(update_error)}"
        )

    retry_in = 60 * (2**task_self.request.retries)
    logger.info(
        f"Retrying scan task for repository {repository_id} in {retry_in} seconds (attempt {task_self.request.retries + 1}/4)"
    )
    task_self.retry(countdown=retry_in, max_retries=3, exc=error)
    return {}


@celery_app.task(bind=True)  # type: ignore[misc]
def scan_repository(
    self: Any, repository_id: str, github_stats: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Scan a single repository for Kubernetes resources using YAMLScanner.

    Args:
        repository_id: UUID string of the repository to scan
        github_stats: Optional GitHub statistics data to pass to metrics task
    """
    logger.info(f"Starting repository scan task for repository_id={repository_id}")

    try:
        with Session(engine) as session:
            repository = get_repository_by_id(session, repository_id)
            repo_workdir = validate_working_directory(repository)

            update_scan_status(session, repository, SyncStatus.SYNCING)

            scan_result = perform_yaml_scan(session, repository, repo_workdir)

            repository.last_scan_total_resources = scan_result.total_resources
            update_scan_status(session, repository, SyncStatus.SUCCESS)

            trigger_metrics_task(repository, scan_result, github_stats)
            return {
                "repository_id": repository_id,
                "repository_name": repository.full_name,
                "working_directory": str(repo_workdir),
                "status": "success",
                "scan_result": {
                    "total_resources": scan_result.total_resources,
                    "created_count": scan_result.created_count,
                    "modified_count": scan_result.modified_count,
                    "deleted_count": scan_result.deleted_count,
                    "scan_duration_seconds": scan_result.scan_duration_seconds,
                },
            }
    except Exception as exc:
        return handle_scan_error(repository_id, exc, self)
