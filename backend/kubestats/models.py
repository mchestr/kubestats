import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from datetime import datetime


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


# Repository Models for GitHub Discovery and Stats


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"


# Shared properties for repositories
class RepositoryBase(SQLModel):
    name: str = Field(max_length=255)
    full_name: str = Field(max_length=255, index=True)  # owner/repo
    owner: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    language: str | None = Field(default=None, max_length=100)
    topics: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    license_name: str | None = Field(default=None, max_length=100)
    default_branch: str = Field(max_length=100, default="main")
    created_at: datetime
    discovery_tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))


# Database model for repositories
class Repository(RepositoryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    github_id: int = Field(unique=True, index=True)
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    # Sync tracking fields
    last_sync_at: datetime | None = Field(default=None, index=True)
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING, index=True)
    sync_error: str | None = Field(default=None, max_length=2000)
    working_directory_path: str | None = Field(default=None, max_length=500)

    # Scan tracking fields
    last_scan_at: datetime | None = Field(default=None, index=True)
    scan_status: SyncStatus = Field(default=SyncStatus.PENDING, index=True)
    scan_error: str | None = Field(default=None, max_length=2000)
    last_scan_total_resources: int | None = Field(default=None)

    # Relationships
    metrics: list["RepositoryMetrics"] = Relationship(
        back_populates="repository", cascade_delete=True
    )
    kubernetes_resources: list["KubernetesResource"] = Relationship(
        back_populates="repository", cascade_delete=True
    )


# Time-series metrics snapshots
class RepositoryMetrics(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repository_id: uuid.UUID = Field(
        foreign_key="repository.id", nullable=False, ondelete="CASCADE"
    )

    # Time-varying metrics
    stars_count: int = Field(default=0)
    forks_count: int = Field(default=0)
    watchers_count: int = Field(default=0)
    open_issues_count: int = Field(default=0)
    size: int = Field(default=0)  # KB

    # Kubernetes resource metrics
    kubernetes_resources_count: int = Field(
        default=0
    )  # Total K8s resources in repository

    # Repository timestamps
    updated_at: datetime  # repo's last update
    pushed_at: datetime | None  # last push

    # Snapshot metadata
    recorded_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    repository: Repository = Relationship(back_populates="metrics")


# API response models
class RepositoryPublic(RepositoryBase):
    id: uuid.UUID
    github_id: int
    discovered_at: datetime
    last_sync_at: datetime | None = None
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_error: str | None = None
    working_directory_path: str | None = None
    last_scan_at: datetime | None = None
    scan_status: SyncStatus = SyncStatus.PENDING
    scan_error: str | None = None
    last_scan_total_resources: int | None = None
    latest_metrics: "RepositoryMetricsPublic | None" = None


class RepositoryMetricsPublic(SQLModel):
    id: uuid.UUID
    stars_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    size: int
    kubernetes_resources_count: int
    updated_at: datetime
    pushed_at: datetime | None
    recorded_at: datetime


class RepositoriesPublic(SQLModel):
    data: list[RepositoryPublic]
    count: int


class RepositoryStatsPublic(SQLModel):
    total_repositories: int
    total_stars: int
    total_forks: int
    languages: dict[str, int]
    top_repositories: list[RepositoryPublic]


# Kubernetes Resource Models for FluxCD YAML Scanning


class KubernetesResource(SQLModel, table=True):
    """Tracks Kubernetes resources found in FluxCD repositories"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repository_id: uuid.UUID = Field(
        foreign_key="repository.id", nullable=False, ondelete="CASCADE", index=True
    )

    # Resource identification
    api_version: str = Field(max_length=100, index=True)
    kind: str = Field(max_length=100, index=True)
    name: str = Field(max_length=255, index=True)
    namespace: str | None = Field(max_length=255, index=True)

    # File location within repository
    file_path: str = Field(max_length=500)  # Relative to repo root
    file_hash: str = Field(max_length=64)  # SHA256 of file content

    # Resource content (parsed)
    resource_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))
    spec: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Lifecycle tracking
    current_status: str = Field(
        max_length=20, default="ACTIVE", index=True
    )  # "ACTIVE", "DELETED"
    deleted_at: datetime | None = Field(index=True)

    # Change tracking
    modification_count: int = Field(default=0)
    last_change_type: str | None = Field(max_length=20)  # Last event type

    # Tracking timestamps
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    repository: Repository = Relationship(back_populates="kubernetes_resources")
    metrics: list["KubernetesResourceMetrics"] = Relationship(
        back_populates="resource", cascade_delete=True
    )
    outgoing_references: list["KubernetesResourceReference"] = Relationship(
        back_populates="source_resource",
        sa_relationship_kwargs={
            "foreign_keys": "[KubernetesResourceReference.source_resource_id]"
        },
    )
    incoming_references: list["KubernetesResourceReference"] = Relationship(
        back_populates="target_resource",
        sa_relationship_kwargs={
            "foreign_keys": "[KubernetesResourceReference.target_resource_id]"
        },
    )
    lifecycle_events: list["ResourceLifecycleEvent"] = Relationship(
        back_populates="resource"
    )

    # Unique constraint: one resource per name/namespace/kind/apiVersion per repository
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "api_version",
            "kind",
            "name",
            "namespace",
            name="uq_k8s_resource_per_repo",
        ),
    )


class KubernetesResourceMetrics(SQLModel, table=True):
    """Time-series metrics for Kubernetes resources"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resource_id: uuid.UUID = Field(
        foreign_key="kubernetesresource.id", nullable=False, ondelete="CASCADE"
    )

    # FluxCD specific version tracking
    chart_version: str | None = Field(
        max_length=100, index=True
    )  # HelmRelease chart version
    chart_name: str | None = Field(
        max_length=255, index=True
    )  # Chart name for trending
    chart_repository: str | None = Field(max_length=500, index=True)  # OCI registry URL
    source_revision: str | None = Field(
        max_length=100, index=True
    )  # Git commit/tag from sourceRef

    # Deployment specific
    image_versions: dict[str, str] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )  # container_name: image_tag
    replicas: int | None = Field()  # For Deployments

    # Reference snapshot - versions of all referenced resources at this point in time
    reference_versions: dict[str, str] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Resource health/status (if available)
    resource_status: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Snapshot metadata
    recorded_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    resource: KubernetesResource = Relationship(back_populates="metrics")


class KubernetesResourceReference(SQLModel, table=True):
    """Tracks references between Kubernetes resources within repositories"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Source resource (the one making the reference)
    source_resource_id: uuid.UUID | None = Field(
        foreign_key="kubernetesresource.id", ondelete="CASCADE"
    )
    source_repository_id: uuid.UUID = Field(
        foreign_key="repository.id", ondelete="CASCADE", index=True
    )

    # Target resource (the one being referenced)
    target_resource_id: uuid.UUID | None = Field(
        foreign_key="kubernetesresource.id", ondelete="CASCADE"
    )
    target_repository_id: uuid.UUID | None = Field(
        foreign_key="repository.id", ondelete="CASCADE", index=True
    )

    # Reference details
    reference_type: str = Field(
        max_length=50, index=True
    )  # e.g., "sourceRef", "configMapRef"
    reference_path: str = Field(max_length=200)  # JSON path in source spec

    # Target identification
    target_name: str = Field(max_length=255, index=True)
    target_namespace: str | None = Field(max_length=255, index=True)
    target_kind: str = Field(max_length=100, index=True)
    target_api_version: str | None = Field(max_length=100)

    # Reference scope
    is_external_reference: bool = Field(
        default=False, index=True
    )  # True if references outside repository
    external_reference_details: dict | None = Field(
        default=None, sa_column=Column(JSON)
    )

    # Version/revision tracking
    referenced_version: str | None = Field(max_length=100, index=True)

    # Tracking
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    source_resource: KubernetesResource = Relationship(
        back_populates="outgoing_references",
        sa_relationship_kwargs={
            "foreign_keys": "[KubernetesResourceReference.source_resource_id]"
        },
    )
    target_resource: KubernetesResource | None = Relationship(
        back_populates="incoming_references",
        sa_relationship_kwargs={
            "foreign_keys": "[KubernetesResourceReference.target_resource_id]"
        },
    )
    source_repository: Repository = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[KubernetesResourceReference.source_repository_id]"
        }
    )
    target_repository: Repository | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[KubernetesResourceReference.target_repository_id]"
        }
    )


class ResourceLifecycleEvent(SQLModel, table=True):
    """Tracks all changes to Kubernetes resources over time for trending analysis"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Resource identification
    resource_id: uuid.UUID | None = Field(
        foreign_key="kubernetesresource.id", ondelete="SET NULL"
    )
    repository_id: uuid.UUID = Field(
        foreign_key="repository.id", ondelete="CASCADE", index=True
    )

    # Resource details (denormalized for historical tracking)
    resource_name: str = Field(max_length=255, index=True)
    resource_namespace: str | None = Field(max_length=255, index=True)
    resource_kind: str = Field(max_length=100, index=True)
    resource_api_version: str = Field(max_length=100, index=True)

    # Event details
    event_type: str = Field(
        max_length=20, index=True
    )  # "CREATED", "MODIFIED", "DELETED"
    event_timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Change details
    file_path: str | None = Field(max_length=500)
    file_hash_before: str | None = Field(max_length=64)
    file_hash_after: str | None = Field(max_length=64)

    # Snapshot of resource content at this point in time
    resource_snapshot: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Change metadata
    changes_detected: list[str] = Field(
        default_factory=list, sa_column=Column(JSON)
    )  # ["spec.image", "spec.replicas"]
    sync_run_id: uuid.UUID | None = Field()  # Links events from same scan

    # Relationships
    resource: KubernetesResource | None = Relationship(
        back_populates="lifecycle_events"
    )
    repository: Repository = Relationship()


class ResourceTrendSnapshot(SQLModel, table=True):
    """Pre-aggregated trend data for efficient querying"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Time window
    snapshot_date: datetime = Field(index=True)  # Daily snapshots
    time_window: str = Field(max_length=20, index=True)  # "daily", "weekly", "monthly"

    # Resource grouping
    resource_kind: str = Field(max_length=100, index=True)
    resource_api_version: str = Field(max_length=100, index=True)

    # For HelmReleases - track chart popularity
    chart_name: str | None = Field(
        max_length=255, index=True
    )  # extracted from HelmRelease
    chart_version: str | None = Field(max_length=100, index=True)
    chart_repository: str | None = Field(max_length=500, index=True)  # OCI registry URL

    # Aggregated metrics
    total_instances: int = Field(default=0, index=True)  # Total across all repos
    active_repositories: int = Field(default=0)  # Number of repos using this resource
    new_adoptions: int = Field(default=0)  # New repos that added this resource
    removals: int = Field(default=0)  # Repos that removed this resource

    # Change velocity
    modifications_count: int = Field(
        default=0
    )  # How often this resource type is modified

    # Version distribution (for charts/images)
    version_distribution: dict[str, int] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Repository breakdown
    repository_breakdown: dict[str, dict] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Creation metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


# API Response Models for Kubernetes Resources


class KubernetesResourcePublic(SQLModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    api_version: str
    kind: str
    name: str
    namespace: str | None
    file_path: str
    resource_metadata: dict
    spec: dict
    current_status: str
    modification_count: int
    last_change_type: str | None
    first_seen_at: datetime
    last_updated_at: datetime
    latest_metrics: "KubernetesResourceMetricsPublic | None" = None


class KubernetesResourceMetricsPublic(SQLModel):
    id: uuid.UUID
    chart_version: str | None
    chart_name: str | None
    chart_repository: str | None
    source_revision: str | None
    image_versions: dict[str, str]
    replicas: int | None
    reference_versions: dict[str, str]
    recorded_at: datetime


class KubernetesResourcesPublic(SQLModel):
    data: list[KubernetesResourcePublic]
    count: int


class ResourceReferencePublic(SQLModel):
    id: uuid.UUID
    reference_type: str
    target_name: str
    target_namespace: str | None
    target_kind: str
    target_api_version: str | None
    referenced_version: str | None
    is_external_reference: bool


class HelmReleaseWithVersionPublic(SQLModel):
    """HelmRelease with resolved chart version information"""

    helm_release: KubernetesResourcePublic
    chart_name: str | None
    chart_version: str | None
    chart_repository: str | None
    oci_repository: KubernetesResourcePublic | None
    version_source: str  # "pinned", "oci_tag", "latest"
    is_version_pinned: bool


class ResourceTrendPublic(SQLModel):
    resource_kind: str
    resource_api_version: str
    chart_name: str | None
    total_instances: int
    active_repositories: int
    growth_trend: int  # new_adoptions - removals
    adoption_velocity: int  # new_adoptions
    modification_frequency: float
    popular_versions: dict[str, int]


class KubernetesStatsPublic(SQLModel):
    total_resources: int
    total_repositories_with_resources: int
    resource_breakdown: dict[str, int]  # resource_kind: count
    popular_charts: list[ResourceTrendPublic]
    recent_trends: list[ResourceTrendPublic]
