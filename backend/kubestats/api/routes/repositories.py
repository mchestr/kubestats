"""
API routes for repository operations.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from kubestats import crud
from kubestats.api.deps import get_current_active_superuser, get_db
from kubestats.models import (
    EventDailyCountsPublic,
    KubernetesResourceEventPublic,
    KubernetesResourceEventsPublic,
    Message,
    RepositoriesPublic,
    RepositoryPublic,
    RepositoryStatsPublic,
    SyncStatus,
)

router = APIRouter()


@router.get("/", response_model=RepositoriesPublic)
def read_repositories(
    session: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
) -> Any:
    """
    Retrieve repositories with pagination.
    """
    repositories = crud.get_repositories_with_latest_metrics(
        session=session, skip=skip, limit=limit
    )

    return RepositoriesPublic(data=repositories, count=len(repositories))


@router.get("/stats", response_model=RepositoryStatsPublic)
def read_repository_stats(
    session: Session = Depends(get_db),
) -> Any:
    """
    Get aggregate repository statistics.
    """
    stats = crud.get_repository_stats(session=session)

    # Get top repositories by stars
    top_repos = crud.get_repositories_with_latest_metrics(
        session=session, skip=0, limit=10
    )
    # Sort by stars count from latest metrics
    top_repos.sort(
        key=lambda r: r.latest_metrics.stars_count if r.latest_metrics else 0,
        reverse=True,
    )

    return RepositoryStatsPublic(
        total_repositories=stats["total_repositories"],
        total_stars=stats["total_stars"],
        total_forks=stats["total_forks"],
        languages=stats["languages"],
        top_repositories=top_repos[:5],  # Top 5 repositories
    )


@router.get("/search", response_model=RepositoriesPublic)
def search_repositories(
    q: str = Query(..., description="Search query"),
    session: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
) -> Any:
    """
    Search repositories by name, description, or topics.
    """
    repositories = crud.search_repositories_with_latest_metrics(
        session=session, query=q, skip=skip, limit=limit
    )

    return RepositoriesPublic(data=repositories, count=len(repositories))


@router.get("/{repository_id}", response_model=RepositoryPublic)
def read_repository(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
) -> Any:
    """
    Get a specific repository by ID.
    """
    repository = crud.get_repository_by_id_with_latest_metrics(
        session=session, repository_id=repository_id
    )
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    return repository


@router.get("/{repository_id}/metrics")
def read_repository_metrics(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
    limit: int = Query(default=100, le=1000),
) -> Any:
    """
    Get metrics history for a specific repository.
    """
    repository = crud.get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    metrics = crud.get_repository_metrics_history(
        session=session, repository_id=repository_id, limit=limit
    )

    return {"data": metrics, "count": len(metrics)}


@router.post(
    "/discover",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def trigger_repository_discovery() -> Any:
    """
    Trigger repository discovery task.
    """
    from kubestats.tasks.discover_repositories import discover_repositories

    try:
        # Trigger the task asynchronously
        task = discover_repositories.delay()
        return Message(message=f"Repository discovery task started: {task.id}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start repository discovery task: {str(e)}",
        )


@router.post(
    "/sync",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def trigger_repository_sync_all(
    db: Session = Depends(get_db),
) -> Any:
    """
    Trigger sync for all repositories.
    """
    from kubestats.tasks.sync_repositories import sync_repository

    repositories = crud.get_repositories(session=db)
    for repository in repositories:
        sync_repository.delay(str(repository.id))
    return Message(
        message=f"Repository sync task started for {len(repositories)} repositories."
    )


@router.post(
    "/{repository_id}/sync",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def trigger_repository_sync_single(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
) -> Any:
    """
    Trigger sync for a specific repository.
    """
    from kubestats.tasks.sync_repositories import sync_repository

    # Verify repository exists
    repository = crud.get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        # Trigger the sync task asynchronously
        task = sync_repository.delay(str(repository_id))
        return Message(
            message=f"Repository sync task started for {repository.full_name}: {task.id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start repository sync task: {str(e)}",
        )


@router.post(
    "/{repository_id}/block",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def block_repository(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
) -> Any:
    """
    Block a repository from being synced.
    Only superusers can block repositories.
    """
    # Verify repository exists
    repository = crud.get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Update sync status to BLOCKED
    repository.sync_status = SyncStatus.BLOCKED
    repository.sync_error = "Repository blocked by administrator"
    session.add(repository)
    session.commit()

    return Message(
        message=f"Repository {repository.full_name} has been blocked from sync"
    )


@router.post(
    "/{repository_id}/approve",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def approve_repository(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
) -> Any:
    """
    Approve a repository for syncing (removes PENDING_APPROVAL or BLOCKED status).
    Only superusers can approve repositories.
    """
    # Verify repository exists
    repository = crud.get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Only allow approval if currently blocked or pending approval
    if repository.sync_status not in [SyncStatus.BLOCKED, SyncStatus.PENDING_APPROVAL]:
        raise HTTPException(
            status_code=400,
            detail=f"Repository is not in a state that requires approval (current status: {repository.sync_status})",
        )

    # Update sync status to PENDING to allow sync
    repository.sync_status = SyncStatus.PENDING
    repository.sync_error = None
    session.add(repository)
    session.commit()

    return Message(
        message=f"Repository {repository.full_name} has been approved for sync"
    )


@router.get("/{repository_id}/events", response_model=KubernetesResourceEventsPublic)
def read_repository_events(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, le=1000),
    event_type: str | None = Query(default=None, description="Filter by event type (CREATED, MODIFIED, DELETED)"),
    resource_kind: str | None = Query(default=None, description="Filter by resource kind"),
    resource_namespace: str | None = Query(default=None, description="Filter by resource namespace"),
) -> Any:
    """
    Get events for a specific repository with pagination and filters.
    """
    # Verify repository exists
    repository = crud.get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get events with filters
    events = crud.get_repository_events(
        session=session,
        repository_id=repository_id,
        skip=skip,
        limit=limit,
        event_type=event_type,
        resource_kind=resource_kind,
        resource_namespace=resource_namespace,
    )

    # Get total count for pagination
    total_count = crud.get_repository_events_count(
        session=session,
        repository_id=repository_id,
        event_type=event_type,
        resource_kind=resource_kind,
        resource_namespace=resource_namespace,
    )

    # Convert to public models
    events_public = [
        KubernetesResourceEventPublic.model_validate(event) for event in events
    ]

    return KubernetesResourceEventsPublic(data=events_public, count=total_count)


@router.get("/{repository_id}/events/daily-counts", response_model=EventDailyCountsPublic)
def read_repository_events_daily_counts(
    repository_id: uuid.UUID,
    session: Session = Depends(get_db),
    days: int = Query(default=30, le=365, description="Number of days to include in the chart"),
) -> Any:
    """
    Get daily event counts for a repository over the specified number of days.
    """
    # Verify repository exists
    repository = crud.get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Get daily counts
    daily_counts = crud.get_repository_events_daily_counts(
        session=session, repository_id=repository_id, days=days
    )

    return EventDailyCountsPublic(data=daily_counts)
