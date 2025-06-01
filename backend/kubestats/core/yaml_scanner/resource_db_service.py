"""
Database service for managing Flux resources and change tracking.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from sqlmodel import Session, select

from kubestats.core.yaml_scanner.models import ChangeSet, ResourceChange, ResourceData, ScanResult
from kubestats.models import KubernetesResource, KubernetesResourceEvent

logger = logging.getLogger(__name__)


class ResourceDatabaseService:
    """Handles database operations for Flux resource scanning."""

    def get_existing_resources(self, session: Session, repository_id: uuid.UUID) -> Dict[str, KubernetesResource]:
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
            KubernetesResource.status == "ACTIVE"
        )
        existing_resources = session.exec(stmt).all()
        
        # Create lookup dictionary using the same key format as ResourceData
        resource_map = {}
        for resource in existing_resources:
            key = resource.resource_key()
            resource_map[key] = resource
            
        logger.info(f"Found {len(resource_map)} existing active resources for repository {repository_id}")
        return resource_map

    def compare_resources(self, existing_resources: Dict[str, KubernetesResource], scanned_resources: List[ResourceData]) -> ChangeSet:
        """
        Compare existing resources with scanned resources to detect changes.
        
        Args:
            existing_resources: Map of resource keys to existing KubernetesResource objects
            scanned_resources: List of ResourceData from current scan
            
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
                    changeset.modified.append(ResourceChange(
                        type="MODIFIED",
                        resource_data=resource_data,
                        existing_resource=existing_resource,
                        file_hash_before=existing_resource.file_hash,
                        file_hash_after=resource_data.file_hash
                    ))
                    logger.debug(f"Modified resource detected: {resource_key}")
                # If hashes match, no change needed
            else:
                # New resource
                changeset.created.append(ResourceChange(
                    type="CREATED",
                    resource_data=resource_data,
                    existing_resource=None,
                    file_hash_before=None,
                    file_hash_after=resource_data.file_hash
                ))
                logger.debug(f"New resource detected: {resource_key}")
        
        # Check for deleted resources
        for resource_key, existing_resource in existing_resources.items():
            if resource_key not in scanned_keys:
                changeset.deleted.append(ResourceChange(
                    type="DELETED",
                    resource_data=None,
                    existing_resource=existing_resource,
                    file_hash_before=existing_resource.file_hash,
                    file_hash_after=None
                ))
                logger.debug(f"Deleted resource detected: {resource_key}")
        
        logger.info(
            f"Change detection complete: {len(changeset.created)} created, "
            f"{len(changeset.modified)} modified, {len(changeset.deleted)} deleted"
        )
        
        return changeset

    def apply_scan_results(
        self, 
        session: Session, 
        repository_id: uuid.UUID, 
        resources: List[ResourceData]
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
            changeset = self.compare_resources(existing_resources, resources)
            
            # Step 3: Apply changes and create lifecycle events
            created_resources = []
            modified_resources = []
            deleted_resources = []
            all_lifecycle_events = []
            
            # Process created resources
            for change in changeset.created:
                resource, event = self._create_resource(session, repository_id, change.resource_data, sync_run_id)
                created_resources.append(resource)
                all_lifecycle_events.append(event)
            
            # Process modified resources  
            for change in changeset.modified:
                resource, event = self._update_resource(session, change.existing_resource, change.resource_data, sync_run_id)
                modified_resources.append(resource)
                all_lifecycle_events.append(event)
            
            # Process deleted resources
            for change in changeset.deleted:
                resource, event = self._delete_resource(session, change.existing_resource, sync_run_id)
                deleted_resources.append(resource)
                all_lifecycle_events.append(event)
            
            # Step 4: Commit all changes
            session.commit()
            
            # Calculate scan duration
            scan_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Step 5: Create scan result
            total_active_resources = len(existing_resources) + len(created_resources) - len(deleted_resources)
            scan_result = ScanResult(
                created_count=len(created_resources),
                modified_count=len(modified_resources),
                deleted_count=len(deleted_resources),
                total_resources=total_active_resources,
                sync_run_id=sync_run_id,
                scan_duration_seconds=scan_duration
            )
            
            logger.info(
                f"Scan completed successfully: "
                f"{scan_result.created_count} created, "
                f"{scan_result.modified_count} modified, "
                f"{scan_result.deleted_count} deleted, "
                f"{scan_result.total_resources} total active resources, "
                f"{scan_duration:.2f}s duration"
            )
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Error applying scan results: {str(e)}")
            session.rollback()
            raise

    def _create_resource(self, session: Session, repository_id: uuid.UUID, resource_data: ResourceData, sync_run_id: uuid.UUID) -> tuple[KubernetesResource, KubernetesResourceEvent]:
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
            updated_at=now
        )
        
        session.add(kubernetes_resource)
        session.flush()  # Get the ID for the lifecycle event
        
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
            sync_run_id=sync_run_id
        )
        
        session.add(lifecycle_event)
        
        logger.debug(f"Created resource {resource_data.resource_key()}")
        return kubernetes_resource, lifecycle_event

    def _update_resource(self, session: Session, existing_resource: KubernetesResource, resource_data: ResourceData, sync_run_id: uuid.UUID) -> tuple[KubernetesResource, KubernetesResourceEvent]:
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
            sync_run_id=sync_run_id
        )
        
        session.add(lifecycle_event)
        
        logger.debug(f"Updated resource {resource_data.resource_key()}")
        return existing_resource, lifecycle_event

    def _delete_resource(self, session: Session, existing_resource: KubernetesResource, sync_run_id: uuid.UUID) -> tuple[KubernetesResource, KubernetesResourceEvent]:
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
            sync_run_id=sync_run_id
        )
        
        session.add(lifecycle_event)
        
        logger.debug(f"Deleted resource {existing_resource.resource_key()}")
        return existing_resource, lifecycle_event

    def get_repository_resource_count(
        self, 
        session: Session, 
        repository_id: uuid.UUID
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
            KubernetesResource.status == "ACTIVE"
        )
        resources = list(session.exec(stmt).all())
        return len(resources)
