"""
API routes for Kubernetes resources and analytics.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, and_, desc, select

from kubestats.api.deps import get_db
from kubestats.models import (
    HelmReleaseWithVersionPublic,
    KubernetesResource,
    KubernetesResourceMetrics,
    KubernetesResourcePublic,
    KubernetesResourceReference,
    KubernetesResourcesPublic,
    KubernetesStatsPublic,
    ResourceLifecycleEvent,
    ResourceReferencePublic,
    ResourceTrendPublic,
    ResourceTrendSnapshot,
)

router = APIRouter()


@router.get("/", response_model=KubernetesResourcesPublic)
def read_kubernetes_resources(
    session: Session = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    repository_id: uuid.UUID | None = Query(default=None),
    resource_kind: str | None = Query(default=None),
    api_version: str | None = Query(default=None),
    namespace: str | None = Query(default=None),
) -> Any:
    """
    Retrieve Kubernetes resources with optional filtering.
    """

    query = select(KubernetesResource).where(
        KubernetesResource.current_status == "ACTIVE"
    )

    # Apply filters
    if repository_id:
        query = query.where(KubernetesResource.repository_id == repository_id)
    if resource_kind:
        query = query.where(KubernetesResource.kind == resource_kind)
    if api_version:
        query = query.where(KubernetesResource.api_version == api_version)
    if namespace:
        query = query.where(KubernetesResource.namespace == namespace)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Get paginated results with latest metrics
    resources = session.exec(
        query.order_by(desc(KubernetesResource.last_updated_at))
        .offset(offset)
        .limit(limit)
    ).all()

    # Convert to public models and include latest metrics
    resources_public = []
    for resource in resources:
        # Get latest metrics
        latest_metrics = session.exec(
            select(KubernetesResourceMetrics)
            .where(KubernetesResourceMetrics.resource_id == resource.id)
            .order_by(desc(KubernetesResourceMetrics.recorded_at))
            .limit(1)
        ).first()

        resource_public = KubernetesResourcePublic.model_validate(resource)
        if latest_metrics:
            resource_public.latest_metrics = latest_metrics

        resources_public.append(resource_public)

    return KubernetesResourcesPublic(data=resources_public, count=count)


@router.get("/stats", response_model=KubernetesStatsPublic)
def read_kubernetes_stats(
    session: Session = Depends(get_db),
) -> Any:
    """
    Get overall Kubernetes resources statistics.
    """

    # Total resources count
    total_resources = session.exec(
        select(func.count(KubernetesResource.id)).where(
            KubernetesResource.current_status == "ACTIVE"
        )
    ).one()

    # Count repositories with Kubernetes resources
    total_repos_with_resources = session.exec(
        select(func.count(func.distinct(KubernetesResource.repository_id))).where(
            KubernetesResource.current_status == "ACTIVE"
        )
    ).one()

    # Resource breakdown by kind
    resource_breakdown_raw = session.exec(
        select(KubernetesResource.kind, func.count(KubernetesResource.id))
        .where(KubernetesResource.current_status == "ACTIVE")
        .group_by(KubernetesResource.kind)
        .order_by(desc(func.count(KubernetesResource.id)))
    ).all()

    resource_breakdown = {row[0]: row[1] for row in resource_breakdown_raw}

    # Get popular charts from recent trends
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    popular_charts_raw = session.exec(
        select(
            ResourceTrendSnapshot.chart_name,
            ResourceTrendSnapshot.resource_api_version,
            func.sum(ResourceTrendSnapshot.total_instances).label("total_instances"),
            func.sum(ResourceTrendSnapshot.active_repositories).label(
                "active_repositories"
            ),
            func.sum(ResourceTrendSnapshot.new_adoptions).label("new_adoptions"),
            func.sum(ResourceTrendSnapshot.removals).label("removals"),
            func.sum(ResourceTrendSnapshot.modifications_count).label("modifications"),
        )
        .where(ResourceTrendSnapshot.snapshot_date >= start_date)
        .where(ResourceTrendSnapshot.chart_name.is_not(None))
        .group_by(
            ResourceTrendSnapshot.chart_name, ResourceTrendSnapshot.resource_api_version
        )
        .order_by(desc("total_instances"))
        .limit(10)
    ).all()

    popular_charts = [
        ResourceTrendPublic(
            resource_kind="HelmRelease",
            resource_api_version=row.resource_api_version,
            chart_name=row.chart_name,
            total_instances=row.total_instances or 0,
            active_repositories=row.active_repositories or 0,
            growth_trend=(row.new_adoptions or 0) - (row.removals or 0),
            adoption_velocity=row.new_adoptions or 0,
            modification_frequency=float(row.modifications or 0)
            / max(row.total_instances or 1, 1),
            popular_versions={},
        )
        for row in popular_charts_raw
    ]

    # Get recent trends
    recent_trends_raw = session.exec(
        select(
            ResourceTrendSnapshot.resource_kind,
            ResourceTrendSnapshot.resource_api_version,
            func.sum(ResourceTrendSnapshot.total_instances).label("total_instances"),
            func.sum(ResourceTrendSnapshot.active_repositories).label(
                "active_repositories"
            ),
            func.sum(ResourceTrendSnapshot.new_adoptions).label("new_adoptions"),
            func.sum(ResourceTrendSnapshot.removals).label("removals"),
            func.sum(ResourceTrendSnapshot.modifications_count).label("modifications"),
        )
        .where(ResourceTrendSnapshot.snapshot_date >= start_date)
        .group_by(
            ResourceTrendSnapshot.resource_kind,
            ResourceTrendSnapshot.resource_api_version,
        )
        .order_by(desc("new_adoptions"))
        .limit(10)
    ).all()

    recent_trends = [
        ResourceTrendPublic(
            resource_kind=row.resource_kind,
            resource_api_version=row.resource_api_version,
            chart_name=None,
            total_instances=row.total_instances or 0,
            active_repositories=row.active_repositories or 0,
            growth_trend=(row.new_adoptions or 0) - (row.removals or 0),
            adoption_velocity=row.new_adoptions or 0,
            modification_frequency=float(row.modifications or 0)
            / max(row.total_instances or 1, 1),
            popular_versions={},
        )
        for row in recent_trends_raw
    ]

    return KubernetesStatsPublic(
        total_resources=total_resources,
        total_repositories_with_resources=total_repos_with_resources,
        resource_breakdown=resource_breakdown,
        popular_charts=popular_charts,
        recent_trends=recent_trends,
    )


@router.get("/{resource_id}", response_model=KubernetesResourcePublic)
def read_kubernetes_resource(
    resource_id: uuid.UUID,
    session: Session = Depends(get_db),
) -> Any:
    """
    Get a specific Kubernetes resource by ID.
    """

    resource = session.get(KubernetesResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Get latest metrics
    latest_metrics = session.exec(
        select(KubernetesResourceMetrics)
        .where(KubernetesResourceMetrics.resource_id == resource.id)
        .order_by(desc(KubernetesResourceMetrics.recorded_at))
        .limit(1)
    ).first()

    resource_public = KubernetesResourcePublic.model_validate(resource)
    if latest_metrics:
        resource_public.latest_metrics = latest_metrics

    return resource_public


@router.get("/{resource_id}/references", response_model=list[ResourceReferencePublic])
def read_resource_references(
    resource_id: uuid.UUID,
    session: Session = Depends(get_db),
) -> Any:
    """
    Get all references made by a specific resource.
    """

    resource = session.get(KubernetesResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    references = session.exec(
        select(KubernetesResourceReference)
        .where(KubernetesResourceReference.source_resource_id == resource_id)
        .order_by(KubernetesResourceReference.reference_type)
    ).all()

    return [ResourceReferencePublic.model_validate(ref) for ref in references]


@router.get("/{resource_id}/history")
def read_resource_history(
    resource_id: uuid.UUID,
    session: Session = Depends(get_db),
    limit: int = Query(default=50, le=100),
) -> Any:
    """
    Get change history for a specific resource.
    """

    resource = session.get(KubernetesResource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    events = session.exec(
        select(ResourceLifecycleEvent)
        .where(ResourceLifecycleEvent.resource_id == resource_id)
        .order_by(desc(ResourceLifecycleEvent.event_timestamp))
        .limit(limit)
    ).all()

    return {
        "resource_id": resource_id,
        "resource_name": resource.name,
        "resource_kind": resource.kind,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "event_timestamp": event.event_timestamp,
                "file_path": event.file_path,
                "changes_detected": event.changes_detected,
                "sync_run_id": event.sync_run_id,
            }
            for event in events
        ],
    }


@router.get("/trends/popular-charts")
def get_popular_helm_charts(
    time_period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    session: Session = Depends(get_db),
) -> Any:
    """Get most popular Helm charts across all repositories"""

    # Calculate date range
    end_date = datetime.utcnow()
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[time_period]
    start_date = end_date - timedelta(days=days)

    # Query trend snapshots
    popular_charts = session.exec(
        select(
            ResourceTrendSnapshot.chart_name,
            ResourceTrendSnapshot.chart_repository,
            func.sum(ResourceTrendSnapshot.total_instances).label("total_usage"),
            func.sum(ResourceTrendSnapshot.active_repositories).label("repo_count"),
            func.sum(ResourceTrendSnapshot.new_adoptions).label("new_adoptions"),
            func.sum(ResourceTrendSnapshot.removals).label("removals"),
        )
        .where(ResourceTrendSnapshot.resource_kind == "HelmRelease")
        .where(ResourceTrendSnapshot.snapshot_date >= start_date)
        .where(ResourceTrendSnapshot.chart_name.is_not(None))
        .group_by(
            ResourceTrendSnapshot.chart_name, ResourceTrendSnapshot.chart_repository
        )
        .order_by(desc("total_usage"))
        .limit(50)
    ).all()

    return {
        "time_period": time_period,
        "popular_charts": [
            {
                "chart_name": chart.chart_name,
                "chart_repository": chart.chart_repository,
                "total_installations": chart.total_usage,
                "repository_count": chart.repo_count,
                "growth_trend": chart.new_adoptions - chart.removals,
                "adoption_velocity": chart.new_adoptions,
            }
            for chart in popular_charts
        ],
    }


@router.get("/trends/resource-adoption")
def get_resource_adoption_trends(
    resource_kind: str | None = Query(default=None),
    time_period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    session: Session = Depends(get_db),
) -> Any:
    """Get adoption trends for Kubernetes resource types"""

    # Calculate date range
    end_date = datetime.utcnow()
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[time_period]
    start_date = end_date - timedelta(days=days)

    query = select(
        ResourceTrendSnapshot.resource_kind,
        ResourceTrendSnapshot.resource_api_version,
        func.sum(ResourceTrendSnapshot.total_instances).label("total_instances"),
        func.sum(ResourceTrendSnapshot.active_repositories).label(
            "active_repositories"
        ),
        func.sum(ResourceTrendSnapshot.new_adoptions).label("new_adoptions"),
        func.sum(ResourceTrendSnapshot.removals).label("removals"),
        func.sum(ResourceTrendSnapshot.modifications_count).label("modifications"),
    ).where(ResourceTrendSnapshot.snapshot_date >= start_date)

    if resource_kind:
        query = query.where(ResourceTrendSnapshot.resource_kind == resource_kind)

    trends = session.exec(
        query.group_by(
            ResourceTrendSnapshot.resource_kind,
            ResourceTrendSnapshot.resource_api_version,
        )
        .order_by(desc("total_instances"))
        .limit(50)
    ).all()

    return {
        "time_period": time_period,
        "resource_kind_filter": resource_kind,
        "trends": [
            {
                "resource_type": f"{trend.resource_api_version}:{trend.resource_kind}",
                "total_instances": trend.total_instances or 0,
                "active_repositories": trend.active_repositories or 0,
                "growth_trend": (trend.new_adoptions or 0) - (trend.removals or 0),
                "adoption_velocity": trend.new_adoptions or 0,
                "modification_frequency": float(trend.modifications or 0)
                / max(trend.total_instances or 1, 1),
            }
            for trend in trends
        ],
    }


@router.get("/helm-releases/with-versions")
def get_helm_releases_with_versions(
    session: Session = Depends(get_db),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    repository_id: uuid.UUID | None = Query(default=None),
) -> Any:
    """
    Get HelmReleases with resolved chart version information.
    """

    # Get HelmReleases with their latest metrics
    query = select(KubernetesResource).where(
        and_(
            KubernetesResource.kind == "HelmRelease",
            KubernetesResource.current_status == "ACTIVE",
        )
    )

    if repository_id:
        query = query.where(KubernetesResource.repository_id == repository_id)

    helm_releases = session.exec(
        query.order_by(desc(KubernetesResource.last_updated_at))
        .offset(offset)
        .limit(limit)
    ).all()

    result = []
    for hr in helm_releases:
        # Get latest metrics
        latest_metrics = session.exec(
            select(KubernetesResourceMetrics)
            .where(KubernetesResourceMetrics.resource_id == hr.id)
            .order_by(desc(KubernetesResourceMetrics.recorded_at))
            .limit(1)
        ).first()

        # Try to find corresponding OCIRepository
        oci_repository = None
        if latest_metrics and latest_metrics.source_revision:
            oci_repo = session.exec(
                select(KubernetesResource).where(
                    and_(
                        KubernetesResource.kind == "OCIRepository",
                        KubernetesResource.name == latest_metrics.source_revision,
                        KubernetesResource.repository_id == hr.repository_id,
                        KubernetesResource.current_status == "ACTIVE",
                    )
                )
            ).first()

            if oci_repo:
                oci_repository = KubernetesResourcePublic.model_validate(oci_repo)

        # Determine version source
        version_source = "latest"
        is_version_pinned = False

        if latest_metrics and latest_metrics.chart_version:
            is_version_pinned = True
            version_source = "pinned"
        elif oci_repository:
            version_source = "oci_tag"

        helm_release_public = KubernetesResourcePublic.model_validate(hr)
        if latest_metrics:
            helm_release_public.latest_metrics = latest_metrics

        result.append(
            HelmReleaseWithVersionPublic(
                helm_release=helm_release_public,
                chart_name=latest_metrics.chart_name if latest_metrics else None,
                chart_version=latest_metrics.chart_version if latest_metrics else None,
                chart_repository=latest_metrics.chart_repository
                if latest_metrics
                else None,
                oci_repository=oci_repository,
                version_source=version_source,
                is_version_pinned=is_version_pinned,
            )
        )

    return {"data": result, "count": len(result)}
