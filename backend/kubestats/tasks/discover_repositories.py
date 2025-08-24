import logging
from datetime import datetime, timezone
from typing import Any

from celery import group  # type: ignore[import-untyped]
from sqlmodel import Session, select

from kubestats.celery_app import celery_app
from kubestats.core.config import settings
from kubestats.core.db import engine
from kubestats.core.github_client import search_repositories
from kubestats.models import Repository, SyncStatus
from kubestats.tasks.sync_repositories import sync_repository

# Set up logging
logger = logging.getLogger(__name__)


def check_repository_size_and_update_status(
    session: Session,
    repository: Repository,
    size_kb: int,
) -> None:
    """Check repository size and update status if it exceeds the threshold."""
    # Convert KB to MB (GitHub API returns size in KB)
    size_mb = size_kb / 1024

    # If repository is > XMB and not already blocked or pending approval, set to pending approval
    if (
        size_mb > settings.GITHUB_MAX_REPOSITORY_SIZE_MB
        and repository.sync_status
        not in [
            SyncStatus.BLOCKED,
            SyncStatus.PENDING_APPROVAL,
        ]
    ):
        logger.warning(
            f"Repository {repository.full_name} is {size_mb:.1f}MB (>{200}MB threshold). "
            f"Setting status to PENDING_APPROVAL."
        )
        repository.sync_status = SyncStatus.PENDING_APPROVAL
        repository.sync_error = f"Repository size ({size_mb:.1f}MB) exceeds the {settings.GITHUB_MAX_REPOSITORY_SIZE_MB}MB threshold and requires approval"
        session.add(repository)
        session.commit()
        logger.info(
            f"Repository {repository.full_name} status updated to PENDING_APPROVAL"
        )


def parse_github_repo(repo_data: dict[str, Any]) -> dict[str, Any]:
    """Parse GitHub repository data into our model format."""
    from kubestats.core.config import settings

    # Extract topics (tags) from the repository
    topics = repo_data.get("topics", [])

    # Parse license information
    license_info = repo_data.get("license")
    license_name = license_info.get("name") if license_info else None

    # Parse dates
    created_at = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))
    updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))

    # Handle pushed_at which might be None
    pushed_at = None
    if repo_data.get("pushed_at"):
        pushed_at = datetime.fromisoformat(
            repo_data["pushed_at"].replace("Z", "+00:00")
        )

    return {
        "github_id": repo_data["id"],
        "name": repo_data["name"],
        "full_name": repo_data["full_name"],
        "owner": repo_data["owner"]["login"],
        "description": repo_data.get("description"),
        "language": repo_data.get("language"),
        "topics": topics,
        "license_name": license_name,
        "default_branch": repo_data.get("default_branch", "main"),
        "created_at": created_at,
        "discovery_tags": [
            tag for tag in settings.GITHUB_DISCOVERY_TAGS if tag in topics
        ],
        # Metrics data
        "stars_count": repo_data.get("stargazers_count", 0),
        "forks_count": repo_data.get("forks_count", 0),
        "watchers_count": repo_data.get("watchers_count", 0),
        "open_issues_count": repo_data.get("open_issues_count", 0),
        "size": repo_data.get("size", 0),
        "updated_at": updated_at,
        "pushed_at": pushed_at,
    }


def create_or_update_repository(
    session: Session, repo_data: dict[str, Any]
) -> tuple[Repository, bool]:
    """Create or update a repository in the database.

    Returns:
        A tuple of (repository, is_new) where is_new is True if this is a newly created repository.
    """
    # Check if repository already exists
    existing_repo = session.exec(
        select(Repository).where(Repository.github_id == repo_data["github_id"])
    ).first()

    if existing_repo:
        # Update existing repository with latest static data
        for key, value in repo_data.items():
            if key not in [
                "stars_count",
                "forks_count",
                "watchers_count",
                "open_issues_count",
                "size",
                "updated_at",
                "pushed_at",
            ]:
                setattr(existing_repo, key, value)
        session.add(existing_repo)
        return existing_repo, False

    # Create new repository
    new_repo = Repository(
        **{
            k: v
            for k, v in repo_data.items()
            if k
            not in [
                "stars_count",
                "forks_count",
                "watchers_count",
                "open_issues_count",
                "size",
                "updated_at",
                "pushed_at",
            ]
        }
    )
    session.add(new_repo)
    return new_repo, True


@celery_app.task()  # type: ignore[misc]
def discover_repositories() -> dict[str, Any]:
    """Discover GitHub repositories with kubesearch or k8s-at-home tags."""
    with Session(engine) as session:
        all_repos = {
            repo["id"]: repo
            for tag in settings.GITHUB_DISCOVERY_TAGS
            for repo in search_repositories(f"topic:{tag}").get("items", [])
        }
        logger.info(f"Found {len(all_repos)} unique repositories across all topics")

        to_sync = []
        new_repos_count = 0
        for repo_data in all_repos.values():
            try:
                parsed_repo_data = parse_github_repo(repo_data)
                repository, is_new = create_or_update_repository(
                    session, parsed_repo_data
                )

                # Check repository size and update status if necessary
                check_repository_size_and_update_status(
                    session, repository, parsed_repo_data["size"]
                )

                # Only sync new repositories
                if is_new:
                    new_repos_count += 1
                    # Extract only stats data for the sync task
                    stats_data = {
                        k: v
                        for k, v in parsed_repo_data.items()
                        if k
                        in [
                            "stars_count",
                            "forks_count",
                            "watchers_count",
                            "open_issues_count",
                            "size",
                            "updated_at",
                            "pushed_at",
                        ]
                    }
                    to_sync.append((str(repository.id), stats_data))
            except Exception as repo_error:
                logger.error(
                    f"Error processing repository {repo_data.get('full_name', 'unknown')}: {str(repo_error)}"
                )
                continue
        session.commit()

    if to_sync:
        sync_tasks = group(
            sync_repository.s(repository_id, stats_data)
            for repository_id, stats_data in to_sync
        )
        sync_tasks.apply_async()
        logger.info(f"Dispatched {len(to_sync)} sync tasks for new repositories")

    logger.info(
        f"Found {new_repos_count} new repositories out of {len(all_repos)} total repositories"
    )

    return {
        "repositories_found": len(all_repos),
        "new_repositories": new_repos_count,
        "repositories_synced": len(to_sync),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
