"""
Repository sync tasks for cloning/updating Git repositories.
"""

import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import git
from sqlmodel import Session, select

from kubestats.celery_app import celery_app
from kubestats.core.config import settings
from kubestats.core.db import engine
from kubestats.models import Repository, SyncStatus
from kubestats.tasks.save_repository_metrics import save_repository_metrics
from kubestats.tasks.scan_repositories import scan_repository

logger = logging.getLogger(__name__)


def update_repository_status(
    session: Session,
    repository: Repository,
    status: SyncStatus,
    error: str | None = None,
) -> None:
    """Update repository sync status."""
    repository.sync_status = status
    repository.sync_error = error[:2000] if error else None
    if status == SyncStatus.SUCCESS:
        repository.last_sync_at = datetime.now(timezone.utc)
    session.add(repository)
    session.commit()


def prepare_working_directory(repository_id: uuid.UUID) -> Path:
    """Prepare and return the working directory path for a repository."""
    repo_workdir = Path(settings.REPO_WORKDIR) / str(repository_id)
    repo_workdir.mkdir(parents=True, exist_ok=True)
    return repo_workdir


def sync_git_repository(repo_workdir: Path, git_url: str, default_branch: str) -> str:
    """Clone or update a git repository."""
    if (repo_workdir / ".git").exists():
        repo_git = git.Repo(repo_workdir)
        origin = repo_git.remotes.origin
        origin.fetch()
        repo_git.git.reset("--hard", f"origin/{default_branch}")
        return "updated"
    git.Repo.clone_from(
        git_url,
        repo_workdir,
        branch=default_branch,
        depth=1,  # Shallow clone to save space
    )
    return "cloned"


def get_repository_by_id(session: Session, repository_id: str) -> Repository:
    """Get repository by ID with error handling."""
    repo_uuid = uuid.UUID(repository_id)
    repository = session.get(Repository, repo_uuid)
    if not repository:
        raise ValueError(f"Repository {repository_id} not found")
    return repository


def handle_sync_error(
    repository_id: str, error: Exception, task_self: Any
) -> dict[str, Any]:
    """Handle sync errors with proper logging and status updates."""
    logger.error(
        f"Error syncing repository {repository_id}: {str(error)}", exc_info=True
    )

    try:
        repo_uuid = uuid.UUID(repository_id)
        with Session(engine) as session:
            repository = session.get(Repository, repo_uuid)
            if repository:
                update_repository_status(
                    session, repository, SyncStatus.ERROR, str(error)
                )
    except Exception as update_error:
        logger.error(
            f"Failed to update error status for repository {repository_id}: {str(update_error)}"
        )

    retry_in = 60 * (2**task_self.request.retries)
    logger.info(
        f"Retrying sync task for repository {repository_id} in {retry_in} seconds (attempt {task_self.request.retries + 1}/4)"
    )
    task_self.retry(countdown=retry_in, max_retries=3, exc=error)
    return {}


@celery_app.task(bind=True)  # type: ignore[misc]
def sync_repository(
    self: Any, repository_id: str, repo_stats: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Sync a single repository by cloning or updating its local copy.

    Args:
        repository_id: UUID string of the repository to sync
        repo_stats: Optional repository metrics data to pass to scan task
    """
    logger.info(f"Starting sync for repository {repository_id}")

    try:
        with Session(engine) as session:
            repository = get_repository_by_id(session, repository_id)

            # Check if repository is blocked or pending approval
            if repository.sync_status == SyncStatus.BLOCKED:
                logger.warning(
                    f"Repository {repository.full_name} is blocked - skipping sync"
                )
                if repo_stats:
                    save_repository_metrics.delay(str(repository.id), 0, repo_stats)

                return {
                    "repository_id": repository_id,
                    "repository_name": repository.full_name,
                    "status": "skipped",
                    "reason": "Repository is blocked by administrator",
                }

            if repository.sync_status == SyncStatus.PENDING_APPROVAL:
                logger.warning(
                    f"Repository {repository.full_name} is pending approval - skipping sync"
                )
                if repo_stats:
                    save_repository_metrics.delay(str(repository.id), 0, repo_stats)

                return {
                    "repository_id": repository_id,
                    "repository_name": repository.full_name,
                    "status": "skipped",
                    "reason": "Repository is pending approval (likely due to size > 200MB)",
                }

            update_repository_status(session, repository, SyncStatus.SYNCING)

            repo_workdir = prepare_working_directory(repository.id)
            git_url = f"https://github.com/{repository.full_name}.git"

            sync_action = sync_git_repository(
                repo_workdir, git_url, repository.default_branch
            )
            logger.info(f"Successfully {sync_action} repository {repository.full_name}")

            repository.working_directory_path = str(repo_workdir)
            update_repository_status(session, repository, SyncStatus.SUCCESS)

            task = scan_repository.delay(str(repository.id), repo_stats)
            logger.info(
                f"Scan task {task.id} triggered for repository {repository.full_name}"
            )

            return {
                "repository_id": repository_id,
                "repository_name": repository.full_name,
                "action": sync_action,
                "working_directory": str(repo_workdir),
                "status": "success",
            }

    except Exception as exc:
        return handle_sync_error(repository_id, exc, self)


def get_active_repository_ids(session: Session) -> set[str]:
    """Get all active repository IDs."""
    active_repos = session.exec(
        select(Repository.id).where(
            Repository.sync_status != SyncStatus.BLOCKED,
            Repository.sync_status != SyncStatus.PENDING_APPROVAL,
        )
    ).all()
    return {str(repo_id) for repo_id in active_repos}


def cleanup_orphaned_directory(item: Path) -> bool:
    """Cleanup a single orphaned directory."""
    try:
        shutil.rmtree(item)
        return True
    except Exception as e:
        logger.error(f"Failed to remove {item}: {e}")
        return False


@celery_app.task()  # type: ignore[misc]
def cleanup_repository_workdirs() -> dict[str, Any]:
    """
    Cleanup old repository working directories that are no longer needed.
    Runs periodically to manage disk space.
    """
    logger.info("Starting repository working directory cleanup")

    try:
        workdir_base = Path(settings.REPO_WORKDIR)
        if not workdir_base.exists():
            return {"message": "Work directory does not exist", "cleaned": 0}

        with Session(engine) as session:
            active_repo_ids = get_active_repository_ids(session)

            cleaned_count = 0
            for item in workdir_base.iterdir():
                if item.is_dir() and item.name not in active_repo_ids:
                    logger.info(f"Removing orphaned directory: {item}")
                    if cleanup_orphaned_directory(item):
                        cleaned_count += 1

        result = {
            "message": f"Cleaned up {cleaned_count} orphaned repository directories",
            "cleaned": cleaned_count,
        }
        logger.info(
            f"Repository cleanup completed: {cleaned_count} directories removed"
        )
        return result

    except Exception as exc:
        logger.error(f"Repository cleanup failed: {str(exc)}", exc_info=True)
        return {"message": f"Cleanup failed: {str(exc)}", "cleaned": 0}
