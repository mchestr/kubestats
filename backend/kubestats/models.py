import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import EmailStr
from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from datetime import datetime


def utc_now() -> datetime:
    """Helper function to get current UTC time, replacing deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)


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
    discovered_at: datetime = Field(default_factory=utc_now)

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
    recorded_at: datetime = Field(default_factory=utc_now, index=True)

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


# Forward reference will be resolved after KubernetesResourcePublic is defined


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


# Simplified Kubernetes Resource Models


class KubernetesResource(SQLModel, table=True):
    """Simplified model that directly persists ResourceData from scanning"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repository_id: uuid.UUID = Field(
        foreign_key="repository.id", nullable=False, ondelete="CASCADE", index=True
    )

    # Core ResourceData fields
    api_version: str = Field(max_length=100, index=True)
    kind: str = Field(max_length=100, index=True)
    name: str = Field(max_length=255, index=True)
    namespace: str | None = Field(max_length=255, index=True)
    file_path: str = Field(max_length=500)
    file_hash: str = Field(max_length=64)  # SHA256 of file content
    version: str | None = Field(max_length=100)  # Resource version if specified
    data: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )  # Full resource spec

    # Lifecycle tracking
    status: str = Field(max_length=20, default="ACTIVE", index=True)  # ACTIVE, DELETED
    deleted_at: datetime | None = Field(index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: datetime = Field(default_factory=utc_now, index=True)

    # Relationships
    repository: Repository = Relationship(back_populates="kubernetes_resources")
    lifecycle_events: list["KubernetesResourceEvent"] = Relationship(
        back_populates="resource", cascade_delete=True
    )

    # Unique constraint: one resource per name/namespace/kind/apiVersion/file_path per repository
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "api_version",
            "kind",
            "name",
            "namespace",
            "file_path",
            name="uq_kubernetes_resource_per_repo",
        ),
    )

    def resource_key(self) -> str:
        """Generate unique key matching ResourceData.resource_key() format"""
        namespace_part = f"{self.namespace}:" if self.namespace else ""
        return f"{self.api_version}:{self.kind}:{namespace_part}{self.name}:{self.file_path}"


class KubernetesResourceEvent(SQLModel, table=True):
    """Simplified lifecycle events for Kubernetes resources"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resource_id: uuid.UUID = Field(
        foreign_key="kubernetesresource.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    repository_id: uuid.UUID = Field(
        foreign_key="repository.id", ondelete="CASCADE", index=True
    )

    # Event details
    event_type: str = Field(max_length=20, index=True)  # CREATED, MODIFIED, DELETED
    event_timestamp: datetime = Field(default_factory=utc_now, index=True)

    # Resource identification (denormalized for fast queries)
    resource_name: str = Field(max_length=255, index=True)
    resource_namespace: str | None = Field(max_length=255, index=True)
    resource_kind: str = Field(max_length=100, index=True)
    resource_api_version: str = Field(max_length=100, index=True)

    # Change tracking
    file_path: str = Field(max_length=500)
    file_hash_before: str | None = Field(max_length=64)
    file_hash_after: str | None = Field(max_length=64)
    changes_detected: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Resource snapshot at time of event
    resource_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Scan grouping
    sync_run_id: uuid.UUID = Field(index=True)

    # Relationships
    resource: KubernetesResource = Relationship(back_populates="lifecycle_events")
    repository: Repository = Relationship()


# API Response Models


class KubernetesResourcePublic(SQLModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    api_version: str
    kind: str
    name: str
    namespace: str | None
    file_path: str
    file_hash: str
    version: str | None
    data: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class KubernetesResourcesPublic(SQLModel):
    data: list[KubernetesResourcePublic]
    count: int


class KubernetesResourceEventPublic(SQLModel):
    id: uuid.UUID
    event_type: str
    event_timestamp: datetime
    resource_name: str
    resource_namespace: str | None
    resource_kind: str
    file_path: str
    changes_detected: list[str]
    sync_run_id: uuid.UUID


class KubernetesResourceEventsPublic(SQLModel):
    data: list[KubernetesResourceEventPublic]
    count: int


class EventDailyCount(SQLModel):
    date: str
    event_type: str
    count: int


class EventDailyCountsPublic(SQLModel):
    data: list[EventDailyCount]
