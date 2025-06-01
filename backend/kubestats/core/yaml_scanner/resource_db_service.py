"""
Database service for managing Flux resources and change tracking.
"""

import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from kubestats.core.yaml_scanner.models import (
    ChangeSet,
    ResourceChange,
    ResourceData,
    ScanResult,
)
from kubestats.models import KubernetesResource, KubernetesResourceEvent


class ResourceDatabaseService:
    """Handles database operations for Flux resource scanning."""

    def get_existing_resources(
        self, session: Session, repository_id: uuid.UUID
    ) -> dict[str, KubernetesResource]:
        """
        Get all existing active resources for a repository, keyed by resource key.

        Args:
            session: Database session
            repository_id: UUID of the repository

        Returns:
            Dictionary mapping resource keys to KubernetesResource objects
        """
        stmt = select(KubernetesResource).where(
            KubernetesResource.repository_id == repository_id,
            KubernetesResource.status == "ACTIVE",
        )
        existing_resources = session.exec(stmt).all()

        # Create lookup dictionary using the same key format as ResourceData
        resource_map = {}
        for resource in existing_resources:
            key = resource.resource_key()
            resource_map[key] = resource
        return resource_map

    def get_deleted_resource(
        self, session: Session, repository_id: uuid.UUID, resource_data: ResourceData
    ) -> KubernetesResource | None:
        """
        Get a deleted resource that matches the given ResourceData for resurrection.

        Args:
            session: Database session
            repository_id: UUID of the repository
            resource_data: ResourceData to match against

        Returns:
            KubernetesResource if found, None otherwise
        """
        stmt = select(KubernetesResource).where(
            KubernetesResource.repository_id == repository_id,
            KubernetesResource.api_version == resource_data.api_version,
            KubernetesResource.kind == resource_data.kind,
            KubernetesResource.name == resource_data.name,
            KubernetesResource.namespace == resource_data.namespace,
            KubernetesResource.status == "DELETED",
        )
        return session.exec(stmt).first()

    def compare_resources(
        self,
        existing_resources: dict[str, KubernetesResource],
        scanned_resources: list[ResourceData],
        session: Session,
        repository_id: uuid.UUID,
    ) -> ChangeSet:
        """
        Compare existing resources with scanned resources to detect changes.

        Args:
            existing_resources: Map of resource keys to existing KubernetesResource objects
            scanned_resources: List of ResourceData from current scan
            session: Database session for checking deleted resources
            repository_id: UUID of the repository

        Returns:
            ChangeSet object containing all detected changes
        """
        changeset = ChangeSet()
        scanned_keys = set()

        # Check each scanned resource for creates/updates
        for resource_data in scanned_resources:
            resource_key = resource_data.resource_key()
            scanned_keys.add(resource_key)

            if resource_key in existing_resources:
                # Resource exists - check for modifications
                existing_resource = existing_resources[resource_key]

                # Compare file hashes to detect content changes
                if existing_resource.file_hash != resource_data.file_hash:
                    changeset.modified.append(
                        ResourceChange(
                            type="MODIFIED",
                            resource_data=resource_data,
                            existing_resource=existing_resource,
                            file_hash_before=existing_resource.file_hash,
                            file_hash_after=resource_data.file_hash,
                        )
                    )
                # If hashes match, no change needed
            else:
                # Resource not found in active resources - check if there's a deleted resource to resurrect
                deleted_resource = self.get_deleted_resource(
                    session, repository_id, resource_data
                )
                if deleted_resource:
                    # This is a resurrection - update the existing deleted resource instead of creating new
                    changeset.modified.append(
                        ResourceChange(
                            type="RESURRECTED",
                            resource_data=resource_data,
                            existing_resource=deleted_resource,
                            file_hash_before=deleted_resource.file_hash,
                            file_hash_after=resource_data.file_hash,
                        )
                    )
                else:
                    # New resource
                    changeset.created.append(
                        ResourceChange(
                            type="CREATED",
                            resource_data=resource_data,
                            existing_resource=None,
                            file_hash_before=None,
                            file_hash_after=resource_data.file_hash,
                        )
                    )

        # Check for deleted resources
        for resource_key, existing_resource in existing_resources.items():
            if resource_key not in scanned_keys:
                changeset.deleted.append(
                    ResourceChange(
                        type="DELETED",
                        resource_data=None,
                        existing_resource=existing_resource,
                        file_hash_before=existing_resource.file_hash,
                        file_hash_after=None,
                    )
                )
        return changeset

    def apply_scan_results(
        self, session: Session, repository_id: uuid.UUID, resources: list[ResourceData]
    ) -> ScanResult:
        """
        Apply scan results to database using proper change detection.

        This method:
        1. Gets existing resources from database
        2. Compares with scanned resources to detect changes
        3. Applies create/update/delete operations
        4. Creates lifecycle events for all changes
        5. Returns scan summary

        Args:
            session: Database session
            repository_id: UUID of the repository
            resources: List of ResourceData objects from scanning

        Returns:
            ScanResult object with operation summary
        """
        sync_run_id = uuid.uuid4()
        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: Get existing resources
            existing_resources = self.get_existing_resources(session, repository_id)

            # Step 2: Detect changes
            changeset = self.compare_resources(
                existing_resources, resources, session, repository_id
            )

            # Step 3: Apply changes and create lifecycle events
            created_resources = []
            modified_resources = []
            deleted_resources = []
            all_lifecycle_events = []

            # Process created resources
            for change in changeset.created:
                resource, event = self._create_resource(
                    session, repository_id, change.resource_data, sync_run_id
                )
                created_resources.append(resource)
                all_lifecycle_events.append(event)

            # Process modified resources
            for change in changeset.modified:
                if change.type == "RESURRECTED":
                    resource, event = self._resurrect_resource(
                        session,
                        change.existing_resource,
                        change.resource_data,
                        sync_run_id,
                    )
                else:
                    resource, event = self._update_resource(
                        session,
                        change.existing_resource,
                        change.resource_data,
                        sync_run_id,
                    )
                modified_resources.append(resource)
                all_lifecycle_events.append(event)

            # Process deleted resources
            for change in changeset.deleted:
                resource, event = self._delete_resource(
                    session, change.existing_resource, sync_run_id
                )
                deleted_resources.append(resource)
                all_lifecycle_events.append(event)

            # Step 4: Commit all changes
            session.commit()

            # Calculate scan duration
            scan_duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Step 5: Create scan result
            total_active_resources = (
                len(existing_resources)
                + len(created_resources)
                - len(deleted_resources)
            )
            scan_result = ScanResult(
                created_count=len(created_resources),
                modified_count=len(modified_resources),
                deleted_count=len(deleted_resources),
                total_resources=total_active_resources,
                sync_run_id=sync_run_id,
                scan_duration_seconds=scan_duration,
            )
            return scan_result

        except Exception:
            session.rollback()
            raise

    def _create_resource(
        self,
        session: Session,
        repository_id: uuid.UUID,
        resource_data: ResourceData,
        sync_run_id: uuid.UUID,
    ) -> tuple[KubernetesResource, KubernetesResourceEvent]:
        """
        Create a new KubernetesResource and its lifecycle event.

        Args:
            session: Database session
            repository_id: Repository UUID
            resource_data: ResourceData to create
            sync_run_id: UUID of current sync run

        Returns:
            Tuple of (created_resource, lifecycle_event)
        """
        now = datetime.now(timezone.utc)

        # Create the resource directly from ResourceData
        kubernetes_resource = KubernetesResource(
            repository_id=repository_id,
            api_version=resource_data.api_version,
            kind=resource_data.kind,
            name=resource_data.name,
            namespace=resource_data.namespace,
            file_path=resource_data.file_path,
            file_hash=resource_data.file_hash,
            version=resource_data.version,
            data=resource_data.data or {},
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )

        session.add(kubernetes_resource)
        session.flush()

        # Create lifecycle event
        lifecycle_event = KubernetesResourceEvent(
            resource_id=kubernetes_resource.id,
            repository_id=repository_id,
            event_type="CREATED",
            event_timestamp=now,
            resource_name=resource_data.name,
            resource_namespace=resource_data.namespace,
            resource_kind=resource_data.kind,
            resource_api_version=resource_data.api_version,
            file_path=resource_data.file_path,
            file_hash_before=None,
            file_hash_after=resource_data.file_hash,
            changes_detected=["resource_created"],
            resource_data=resource_data.data or {},
            sync_run_id=sync_run_id,
        )

        session.add(lifecycle_event)
        return kubernetes_resource, lifecycle_event

    def _resurrect_resource(
        self,
        session: Session,
        existing_resource: KubernetesResource,
        resource_data: ResourceData,
        sync_run_id: uuid.UUID,
    ) -> tuple[KubernetesResource, KubernetesResourceEvent]:
        """
        Resurrect a deleted KubernetesResource and create its lifecycle event.

        Args:
            session: Database session
            existing_resource: Previously deleted KubernetesResource to resurrect
            resource_data: New ResourceData to update the resource with
            sync_run_id: UUID of current sync run

        Returns:
            Tuple of (resurrected_resource, lifecycle_event)
        """
        now = datetime.now(timezone.utc)
        old_hash = existing_resource.file_hash

        # Update the resource with new data and mark as active
        existing_resource.file_path = resource_data.file_path
        existing_resource.file_hash = resource_data.file_hash
        existing_resource.version = resource_data.version
        existing_resource.data = resource_data.data or {}
        existing_resource.status = "ACTIVE"
        existing_resource.deleted_at = None
        existing_resource.updated_at = now

        session.add(existing_resource)

        # Create lifecycle event
        lifecycle_event = KubernetesResourceEvent(
            resource_id=existing_resource.id,
            repository_id=existing_resource.repository_id,
            event_type="RESURRECTED",
            event_timestamp=now,
            resource_name=existing_resource.name,
            resource_namespace=existing_resource.namespace,
            resource_kind=existing_resource.kind,
            resource_api_version=existing_resource.api_version,
            file_path=resource_data.file_path,
            file_hash_before=old_hash,
            file_hash_after=resource_data.file_hash,
            changes_detected=["resource_resurrected"],
            resource_data=resource_data.data or {},
            sync_run_id=sync_run_id,
        )

        session.add(lifecycle_event)
        return existing_resource, lifecycle_event

    def _update_resource(
        self,
        session: Session,
        existing_resource: KubernetesResource,
        resource_data: ResourceData,
        sync_run_id: uuid.UUID,
    ) -> tuple[KubernetesResource, KubernetesResourceEvent]:
        """
        Update an existing KubernetesResource and create its lifecycle event.

        Args:
            session: Database session
            existing_resource: Existing KubernetesResource to update
            resource_data: New ResourceData
            sync_run_id: UUID of current sync run

        Returns:
            Tuple of (updated_resource, lifecycle_event)
        """
        now = datetime.now(timezone.utc)
        old_hash = existing_resource.file_hash

        # Detect what changed
        changes_detected = []
        if existing_resource.file_hash != resource_data.file_hash:
            changes_detected.append("file_content")
        if existing_resource.file_path != resource_data.file_path:
            changes_detected.append("file_path")
        if existing_resource.version != resource_data.version:
            changes_detected.append("version")

        # Update the resource with new data
        existing_resource.file_path = resource_data.file_path
        existing_resource.file_hash = resource_data.file_hash
        existing_resource.version = resource_data.version
        existing_resource.data = resource_data.data or {}
        existing_resource.updated_at = now

        session.add(existing_resource)

        # Create lifecycle event
        lifecycle_event = KubernetesResourceEvent(
            resource_id=existing_resource.id,
            repository_id=existing_resource.repository_id,
            event_type="MODIFIED",
            event_timestamp=now,
            resource_name=existing_resource.name,
            resource_namespace=existing_resource.namespace,
            resource_kind=existing_resource.kind,
            resource_api_version=existing_resource.api_version,
            file_path=resource_data.file_path,
            file_hash_before=old_hash,
            file_hash_after=resource_data.file_hash,
            changes_detected=changes_detected,
            resource_data=resource_data.data or {},
            sync_run_id=sync_run_id,
        )

        session.add(lifecycle_event)
        return existing_resource, lifecycle_event

    def _delete_resource(
        self,
        session: Session,
        existing_resource: KubernetesResource,
        sync_run_id: uuid.UUID,
    ) -> tuple[KubernetesResource, KubernetesResourceEvent]:
        """
        Mark a KubernetesResource as deleted and create its lifecycle event.

        Args:
            session: Database session
            existing_resource: KubernetesResource to mark as deleted
            sync_run_id: UUID of current sync run

        Returns:
            Tuple of (deleted_resource, lifecycle_event)
        """
        now = datetime.now(timezone.utc)

        # Mark resource as deleted (soft delete)
        existing_resource.status = "DELETED"
        existing_resource.deleted_at = now
        existing_resource.updated_at = now

        session.add(existing_resource)

        # Create lifecycle event
        lifecycle_event = KubernetesResourceEvent(
            resource_id=existing_resource.id,
            repository_id=existing_resource.repository_id,
            event_type="DELETED",
            event_timestamp=now,
            resource_name=existing_resource.name,
            resource_namespace=existing_resource.namespace,
            resource_kind=existing_resource.kind,
            resource_api_version=existing_resource.api_version,
            file_path=existing_resource.file_path,
            file_hash_before=existing_resource.file_hash,
            file_hash_after=None,
            changes_detected=["resource_deleted"],
            resource_data=existing_resource.data,
            sync_run_id=sync_run_id,
        )

        session.add(lifecycle_event)
        return existing_resource, lifecycle_event

    def get_repository_resource_count(
        self, session: Session, repository_id: uuid.UUID
    ) -> int:
        """
        Get the current count of active resources for a repository.

        Args:
            session: Database session
            repository_id: UUID of the repository

        Returns:
            Count of active resources
        """
        stmt = select(KubernetesResource).where(
            KubernetesResource.repository_id == repository_id,
            KubernetesResource.status == "ACTIVE",
        )
        resources = list(session.exec(stmt).all())
        return len(resources)
