"""
Data models for YAML scanning operations
"""

import uuid
from dataclasses import dataclass
from typing import Any

from kubestats.models import KubernetesResource


@dataclass
class ResourceData:
    """Parsed Kubernetes resource data"""

    api_version: str
    kind: str
    file_path: str
    file_hash: str

    name: str | None = None
    namespace: str | None = None
    version: str | None = None
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_version": self.api_version,
            "kind": self.kind,
            "name": self.name,
            "namespace": self.namespace,
            "file_path": self.file_path,
            "version": self.version,
            "data": self.data,
        }

    def resource_key(self) -> str:
        """Generate unique key for this resource within repository"""
        namespace_part = f"{self.namespace}:" if self.namespace else ""
        return f"{self.api_version}:{self.kind}:{namespace_part}{self.name}"


@dataclass
class ResourceChange:
    """Represents a change to a Kubernetes resource"""

    type: str  # "CREATED", "MODIFIED", "DELETED"
    resource_data: ResourceData | None = None
    existing_resource: KubernetesResource | None = None
    file_hash_before: str | None = None
    file_hash_after: str | None = None
    detailed_changes: list[str] | None = None

    @property
    def resource_name(self) -> str:
        if self.resource_data:
            return self.resource_data.name
        elif self.existing_resource:
            return self.existing_resource.name
        return "unknown"

    @property
    def resource_namespace(self) -> str | None:
        if self.resource_data:
            return self.resource_data.namespace
        elif self.existing_resource:
            return self.existing_resource.namespace
        return None

    @property
    def resource_kind(self) -> str:
        if self.resource_data:
            return self.resource_data.kind
        elif self.existing_resource:
            return self.existing_resource.kind
        return "unknown"

    @property
    def resource_api_version(self) -> str:
        if self.resource_data:
            return self.resource_data.api_version
        elif self.existing_resource:
            return self.existing_resource.api_version
        return "unknown"

    @property
    def file_path(self) -> str | None:
        if self.resource_data:
            return self.resource_data.file_path
        elif self.existing_resource:
            return self.existing_resource.file_path
        return None


@dataclass
class ChangeSet:
    """Collection of all changes detected during a scan"""

    created: list[ResourceChange]
    modified: list[ResourceChange]
    deleted: list[ResourceChange]

    def __init__(self):
        self.created = []
        self.modified = []
        self.deleted = []


@dataclass
class ScanResult:
    """Results of a repository scan"""

    created_count: int
    modified_count: int
    deleted_count: int
    total_resources: int
    sync_run_id: uuid.UUID
    scan_duration_seconds: float
