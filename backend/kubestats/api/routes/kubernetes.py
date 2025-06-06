import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_
from sqlmodel import Session, select

from kubestats.api.deps import get_db
from kubestats.models import (
    GroupedKubernetesResource,
    GroupedKubernetesResourcesPublic,
    GroupedRepositoryBreakdown,
    KubernetesResource,
    KubernetesResourcesPublic,
    Repository,
)

router = APIRouter()


@router.get("/resources", response_model=KubernetesResourcesPublic)
def list_kubernetes_resources(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repository_id: uuid.UUID | None = None,
    kind: str | None = None,
    api_version: str | None = None,
    namespace: str | None = None,
    status: str | None = None,
) -> KubernetesResourcesPublic:
    """
    List Kubernetes resources with optional filtering.

    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        repository_id: Filter by repository ID
        kind: Filter by resource kind
        api_version: Filter by API version
        namespace: Filter by namespace
    """
    query = select(KubernetesResource).join(Repository)

    # Apply filters if provided
    if repository_id:
        query = query.where(KubernetesResource.repository_id == repository_id)
    if kind:
        query = query.where(KubernetesResource.kind == kind)
    if api_version:
        query = query.where(KubernetesResource.api_version == api_version)
    if namespace:
        query = query.where(KubernetesResource.namespace == namespace)
    if status:
        status_values = status.split(",") if status else []
        if status_values:
            query = query.where(KubernetesResource.status.in_(status_values))  # type: ignore[attr-defined]

    # Get total count
    total = db.exec(select(func.count()).select_from(query.subquery())).first()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    resources = db.exec(query).all()

    return KubernetesResourcesPublic(data=resources, count=total)


@router.get("/resources/grouped", response_model=GroupedKubernetesResourcesPublic)
def list_grouped_kubernetes_resources(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repository_id: uuid.UUID | None = None,
    kind: str | None = None,
    api_version: str | None = None,
    namespace: str | None = None,
    status: str | None = None,
) -> GroupedKubernetesResourcesPublic:
    """
    List Kubernetes resources grouped by kind and name, with repository breakdowns.
    """
    from sqlmodel import select

    # Build base query with filters
    query = select(  # type: ignore[call-overload]
        KubernetesResource.kind,
        KubernetesResource.name,
        Repository.id,
        Repository.full_name,
        func.count().label("count"),
    ).join(Repository)

    if repository_id:
        query = query.where(KubernetesResource.repository_id == repository_id)
    if kind:
        query = query.where(KubernetesResource.kind == kind)
    if api_version:
        query = query.where(KubernetesResource.api_version == api_version)
    if namespace:
        query = query.where(KubernetesResource.namespace == namespace)
    if status:
        status_values = status.split(",") if status else []
        if status_values:
            query = query.where(KubernetesResource.status.in_(status_values))  # type: ignore[attr-defined]

    query = query.group_by(
        KubernetesResource.kind,
        KubernetesResource.name,
        Repository.id,
        Repository.full_name,
    )

    # Subquery to get total counts per (kind, name)
    subq = select(
        KubernetesResource.kind,
        KubernetesResource.name,
        func.count().label("total_count"),
    ).join(Repository)

    if repository_id:
        subq = subq.where(KubernetesResource.repository_id == repository_id)
    if kind:
        subq = subq.where(KubernetesResource.kind == kind)
    if api_version:
        subq = subq.where(KubernetesResource.api_version == api_version)
    if namespace:
        subq = subq.where(KubernetesResource.namespace == namespace)
    if status:
        status_values = status.split(",") if status else []
        if status_values:
            subq = subq.where(KubernetesResource.status.in_(status_values))  # type: ignore[attr-defined]

    subq = subq.group_by(KubernetesResource.kind, KubernetesResource.name)
    subq = subq.offset(skip).limit(limit)

    subq_results = db.exec(subq).all()
    # {(kind, name): total_count}
    group_keys = [(row[0], row[1]) for row in subq_results]
    total_count = len(group_keys)
    if not group_keys:
        return GroupedKubernetesResourcesPublic(data=[], count=0)

    # Now get all repository breakdowns for these group keys
    if group_keys:
        repo_query = query.where(
            or_(
                *[
                    and_(KubernetesResource.kind == k, KubernetesResource.name == n)  # type: ignore[arg-type]
                    for k, n in group_keys
                ]
            )
        )
        repo_results = db.exec(repo_query).all()
    else:
        repo_results = []

    # Organize by (kind, name)
    group_map: dict[tuple[str, str], list[GroupedRepositoryBreakdown]] = {}
    for row in repo_results:
        key = (row[0], row[1])
        if key not in group_map:
            group_map[key] = []
        group_map[key].append(
            GroupedRepositoryBreakdown(
                repository_id=row[2],
                repository_name=row[3],
                count=row[4],
            )
        )

    # Build response
    data = []
    for row in subq_results:
        key = (row[0], row[1])
        data.append(
            GroupedKubernetesResource(
                kind=row[0],
                name=row[1],
                total_count=row[2],
                repositories=group_map.get(key, []),
            )
        )
    return GroupedKubernetesResourcesPublic(data=data, count=total_count)
