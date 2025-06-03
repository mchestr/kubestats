from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select

from kubestats.api.deps import get_db
from kubestats.models import KubernetesResource, KubernetesResourcesPublic, Repository

router = APIRouter(prefix="/kubernetes", tags=["kubernetes"])


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
        query = query.where(KubernetesResource.status.in_(status.split(",")))

    # Get total count
    total = db.exec(select(func.count()).select_from(query.subquery())).first()

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    resources = db.exec(query).all()

    return KubernetesResourcesPublic(data=resources, count=total)
