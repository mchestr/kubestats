import uuid
from typing import Any

from sqlalchemy import desc, func, or_
from sqlmodel import Session, select

from kubestats.core.security import get_password_hash, verify_password
from kubestats.models import (
    KubernetesResource,
    Repository,
    RepositoryMetrics,
    RepositoryMetricsPublic,
    RepositoryPublic,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    print(f"Authenticating user: {email}, found: {db_user is not None}")
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def get_worker_stats_by_id(*, worker_id: str) -> dict[str, Any] | None:
    """
    Retrieves Celery worker statistics for a specific worker.
    Returns comprehensive worker stats including uptime, memory usage, and task counts.
    """
    from kubestats.celery_app import celery_app

    try:
        # Get inspection interface
        i = celery_app.control.inspect()

        # Get worker statistics
        stats_data = i.stats() or {}

        # Look for the specific worker
        for worker_name, worker_info in stats_data.items():
            if worker_name == worker_id or worker_name.endswith(f"@{worker_id}"):
                # Extract key statistics from worker info and return in the new format
                return {
                    "worker_id": worker_id,
                    "worker_name": worker_name,
                    "status": "ONLINE",  # Worker is online if we can get stats
                    "uptime": worker_info.get("uptime", 0),
                    "pid": worker_info.get("pid"),
                    "clock": worker_info.get("clock", 0),
                    "prefetch_count": worker_info.get("prefetch_count", 0),
                    "pool": worker_info.get("pool", {}),
                    "broker": worker_info.get("broker", {}),
                    "total_tasks": worker_info.get("total", {}),
                    "rusage": worker_info.get("rusage", {}),
                }

        # If not found in stats, try to ping the specific worker
        ping_data = i.ping() or {}
        for worker_name, ping_response in ping_data.items():
            if (
                worker_name == worker_id or worker_name.endswith(f"@{worker_id}")
            ) and ping_response.get("ok") == "pong":
                return {
                    "worker_id": worker_id,
                    "worker_name": worker_name,
                    "status": "ONLINE",
                    "uptime": None,
                    "pid": None,
                    "clock": None,
                    "prefetch_count": None,
                    "pool": None,
                    "broker": None,
                    "total_tasks": None,
                    "rusage": None,
                }

        # Worker not found
        return None

    except Exception as e:
        print(f"Error retrieving worker stats from Celery for {worker_id}: {e}")
        # Return None if there's an error
        return None


# Repository CRUD operations


def get_repositories(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[Repository]:
    """Get a list of repositories with optional pagination."""
    statement = select(Repository).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_repository_by_github_id(
    *, session: Session, github_id: int
) -> Repository | None:
    """Get a repository by its GitHub ID."""
    statement = select(Repository).where(Repository.github_id == github_id)
    return session.exec(statement).first()


def get_repository_by_id(
    *, session: Session, repository_id: uuid.UUID
) -> Repository | None:
    """Get a repository by its internal ID."""
    statement = select(Repository).where(Repository.id == repository_id)
    return session.exec(statement).first()


def get_repository_by_id_with_latest_metrics(
    *, session: Session, repository_id: uuid.UUID
) -> RepositoryPublic | None:
    """Get a repository by its internal ID with latest metrics."""
    repository = get_repository_by_id(session=session, repository_id=repository_id)
    if not repository:
        return None

    return _convert_repository_to_public_with_metrics(repository)


def get_repositories_with_latest_metrics(
    *, session: Session, skip: int = 0, limit: int = 100
) -> list[RepositoryPublic]:
    """Get repositories with their latest metrics."""

    # Get repositories with metrics
    statement = select(Repository).offset(skip).limit(limit)
    repositories = list(session.exec(statement).all())

    result = []
    for repo in repositories:
        repo_public = _convert_repository_to_public_with_metrics(repo)
        result.append(repo_public)

    return result


def _convert_repository_to_public_with_metrics(repo: Repository) -> RepositoryPublic:
    """Helper function to convert a Repository to RepositoryPublic with latest_metrics."""
    # Get the latest metrics for this repository
    latest_metrics_public = None
    if repo.metrics:
        latest_metrics = max(repo.metrics, key=lambda m: m.recorded_at)
        latest_metrics_public = RepositoryMetricsPublic.model_validate(latest_metrics)

    repo_public = RepositoryPublic.model_validate(repo)
    repo_public.latest_metrics = latest_metrics_public
    return repo_public


def get_repository_metrics_history(
    *, session: Session, repository_id: uuid.UUID, limit: int = 100
) -> list[RepositoryMetrics]:
    """Get metrics history for a specific repository."""
    statement = (
        select(RepositoryMetrics)
        .where(RepositoryMetrics.repository_id == repository_id)
        .order_by(desc(RepositoryMetrics.recorded_at))  # type: ignore[arg-type]
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_repository_stats(*, session: Session) -> dict[str, Any]:
    """Get aggregate statistics for all repositories."""

    # Get total repository count
    total_repos = session.exec(select(func.count()).select_from(Repository)).one()

    # Get latest metrics for each repository to calculate totals
    latest_metrics_subquery = (
        select(
            RepositoryMetrics.repository_id,
            func.max(RepositoryMetrics.recorded_at).label("max_recorded_at"),
        )
        .group_by(RepositoryMetrics.repository_id)  # type: ignore[arg-type]
        .subquery()
    )

    latest_metrics_query = select(RepositoryMetrics).join(
        latest_metrics_subquery,
        (RepositoryMetrics.repository_id == latest_metrics_subquery.c.repository_id)
        & (RepositoryMetrics.recorded_at == latest_metrics_subquery.c.max_recorded_at),  # type: ignore[arg-type]
    )

    latest_metrics = list(session.exec(latest_metrics_query).all())

    total_stars = sum(metrics.stars_count for metrics in latest_metrics)
    total_forks = sum(metrics.forks_count for metrics in latest_metrics)

    # Get language distribution
    language_query = (
        select(Repository.language, func.count())
        .where(Repository.language.is_not(None))  # type: ignore[union-attr]
        .group_by(Repository.language)
    )
    language_results = session.exec(language_query).all()
    languages = {lang: count for lang, count in language_results if lang}

    return {
        "total_repositories": total_repos,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "languages": languages,
    }


def search_repositories(
    *, session: Session, query: str, skip: int = 0, limit: int = 100
) -> list[Repository]:
    """Search repositories by name, description, or topics."""

    search_term = f"%{query}%"

    statement = (
        select(Repository)
        .where(
            or_(
                Repository.name.ilike(search_term),  # type: ignore[attr-defined]
                Repository.full_name.ilike(search_term),  # type: ignore[attr-defined]
                Repository.description.ilike(search_term),  # type: ignore[union-attr]
                func.array_to_string(Repository.topics, ",").ilike(search_term),
            )
        )
        .offset(skip)
        .limit(limit)
    )

    return list(session.exec(statement).all())


def search_repositories_with_latest_metrics(
    *, session: Session, query: str, skip: int = 0, limit: int = 100
) -> list[RepositoryPublic]:
    """Search repositories by name, description, or topics with latest metrics."""
    repositories = search_repositories(
        session=session, query=query, skip=skip, limit=limit
    )

    result = []
    for repo in repositories:
        repo_public = _convert_repository_to_public_with_metrics(repo)
        result.append(repo_public)

    return result


# Kubernetes Resource CRUD operations


def get_kubernetes_resources_by_repository(
    *, session: Session, repository_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list["KubernetesResource"]:
    """Get Kubernetes resources for a specific repository."""
    from kubestats.models import KubernetesResource

    statement = (
        select(KubernetesResource)
        .where(KubernetesResource.repository_id == repository_id)
        .where(KubernetesResource.current_status == "ACTIVE")
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def cleanup_kubernetes_resources(*, session: Session, repository_id: uuid.UUID) -> int:
    """Remove all Kubernetes resources for a repository."""
    from kubestats.models import KubernetesResource

    # Count existing resources before deletion
    count_stmt = select(KubernetesResource).where(
        KubernetesResource.repository_id == repository_id
    )
    existing_count = len(list(session.exec(count_stmt).all()))

    # Delete all resources for this repository
    from sqlmodel import delete

    delete_stmt = delete(KubernetesResource).where(
        KubernetesResource.repository_id == repository_id
    )
    session.exec(delete_stmt)

    return existing_count


def get_kubernetes_resource_by_id(
    *, session: Session, resource_id: uuid.UUID
) -> "KubernetesResource | None":
    """Get a Kubernetes resource by ID."""
    from kubestats.models import KubernetesResource

    statement = select(KubernetesResource).where(KubernetesResource.id == resource_id)
    return session.exec(statement).first()


def get_kubernetes_resources_stats(
    *, session: Session, repository_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """Get statistics for Kubernetes resources."""
    from kubestats.models import KubernetesResource

    base_query = select(KubernetesResource).where(
        KubernetesResource.current_status == "ACTIVE"
    )

    if repository_id:
        base_query = base_query.where(KubernetesResource.repository_id == repository_id)

    resources = list(session.exec(base_query).all())

    # Calculate statistics
    total_resources = len(resources)

    # Group by kind
    kind_counts = {}
    namespace_counts = {}

    for resource in resources:
        # Count by kind
        kind_key = f"{resource.api_version}/{resource.kind}"
        kind_counts[kind_key] = kind_counts.get(kind_key, 0) + 1

        # Count by namespace
        namespace = resource.namespace or "<cluster-scoped>"
        namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1

    return {
        "total_resources": total_resources,
        "resource_types": kind_counts,
        "namespaces": namespace_counts,
    }


def search_kubernetes_resources(
    *,
    session: Session,
    query: str,
    repository_id: uuid.UUID | None = None,
    kind: str | None = None,
    namespace: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[KubernetesResource]:
    """Search Kubernetes resources with filters."""
    from kubestats.models import KubernetesResource

    search_term = f"%{query}%"

    statement = (
        select(KubernetesResource)
        .where(KubernetesResource.current_status == "ACTIVE")
        .where(
            or_(
                KubernetesResource.name.ilike(search_term),  # type: ignore[attr-defined]
                KubernetesResource.file_path.ilike(search_term),  # type: ignore[attr-defined]
                KubernetesResource.kind.ilike(search_term),  # type: ignore[attr-defined]
            )
        )
    )

    if repository_id:
        statement = statement.where(KubernetesResource.repository_id == repository_id)

    if kind:
        statement = statement.where(KubernetesResource.kind == kind)

    if namespace:
        statement = statement.where(KubernetesResource.namespace == namespace)

    statement = statement.offset(skip).limit(limit)

    return list(session.exec(statement).all())
