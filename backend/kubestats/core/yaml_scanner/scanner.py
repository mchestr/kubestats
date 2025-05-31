"""
Main YAML scanner that orchestrates the scanning process
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from kubestats.models import (
    KubernetesResource,
    Repository,
    ResourceLifecycleEvent,
)

from .change_detector import ChangeDetector
from .models import ChangeSet, ResourceData, ScanResult
from .parser import YAMLParser
from .resource_extractor import ResourceExtractor


class YAMLScanner:
    """Scans FluxCD repositories for Kubernetes resources"""

    def __init__(self, session: Session | None = None):
        self.session = session
        self.parser = YAMLParser()
        self.change_detector = ChangeDetector()
        self.resource_extractor = ResourceExtractor(session) if session else None
        self.logger = logging.getLogger(__name__)

    def scan_repository(self, repository: Repository, repo_path: Path) -> ScanResult:
        """Scan a repository and detect all changes since last scan"""
        start_time = datetime.now(timezone.utc)
        sync_run_id = uuid.uuid4()

        self.logger.info(
            f"Starting scan for repository {repository.full_name} "
            f"(ID: {repository.id}) at path: {repo_path} "
            f"with sync_run_id: {sync_run_id}"
        )

        try:
            # 1. Get current resources from database
            self.logger.debug("Step 1: Getting current resources from database")
            current_resources = self._get_current_resources(repository.id)
            self.logger.info(
                f"Found {len(current_resources)} existing resources in database"
            )

            # 2. Scan filesystem for current state
            self.logger.debug("Step 2: Scanning filesystem for current state")
            filesystem_resources = self.parser.scan_filesystem(repo_path)
            self.logger.info(
                f"Found {len(filesystem_resources)} resources in filesystem"
            )

            # 3. Detect changes
            self.logger.debug(
                "Step 3: Detecting changes between current and filesystem resources"
            )
            changes = self.change_detector.detect_changes(
                current_resources, filesystem_resources
            )
            self.logger.info(
                f"Changes detected - Created: {len(changes.created)}, "
                f"Modified: {len(changes.modified)}, "
                f"Deleted: {len(changes.deleted)}"
            )

            # 4. Record lifecycle events
            self.logger.debug("Step 4: Recording lifecycle events")
            self._record_lifecycle_events(changes, repository.id, sync_run_id)

            # 5. Update resources and create metrics
            self.logger.debug("Step 5: Updating resources and creating metrics")
            self._update_resources(changes, repository.id)

            # 6. Extract and store resource references
            if self.resource_extractor:
                self.logger.debug("Step 6: Extracting and storing resource references")
                self.resource_extractor.extract_resource_references(
                    filesystem_resources, repository.id
                )
                self.logger.debug("Resource references extraction completed")
            else:
                self.logger.debug(
                    "Step 6: Skipping resource references extraction (no session)"
                )

            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            scan_result = ScanResult(
                created_count=len(changes.created),
                modified_count=len(changes.modified),
                deleted_count=len(changes.deleted),
                total_resources=len(filesystem_resources),
                sync_run_id=sync_run_id,
                scan_duration_seconds=duration,
            )

            self.logger.info(
                f"Scan completed successfully for repository {repository.full_name} "
                f"in {duration:.2f} seconds. "
                f"Results: {scan_result.created_count} created, "
                f"{scan_result.modified_count} modified, "
                f"{scan_result.deleted_count} deleted, "
                f"{scan_result.total_resources} total resources"
            )

            return scan_result

        except Exception as e:
            self.logger.error(
                f"Scan failed for repository {repository.full_name} "
                f"(ID: {repository.id}) at path: {repo_path}. Error: {str(e)}",
                exc_info=True,
            )
            if self.session:
                self.logger.debug("Rolling back database session due to error")
                self.session.rollback()
            raise Exception(
                f"Failed to scan repository {repository.full_name}: {str(e)}"
            )

    def _get_current_resources(
        self, repository_id: uuid.UUID
    ) -> dict[str, KubernetesResource]:
        """Get all current active resources for the repository"""
        self.logger.debug(f"Getting current resources for repository: {repository_id}")
        if not self.session:
            self.logger.warning(
                "No database session available, returning empty resources dict"
            )
            return {}

        resources = self.session.exec(
            select(KubernetesResource)
            .where(KubernetesResource.repository_id == repository_id)
            .where(KubernetesResource.current_status == "ACTIVE")
        ).all()

        resource_dict = {self._resource_key(r): r for r in resources}
        self.logger.debug(
            f"Retrieved {len(resources)} active resources from database: "
            f"{list(resource_dict.keys())}"
        )
        return resource_dict

    def _resource_key(self, resource: KubernetesResource) -> str:
        """Generate unique key for a resource"""
        namespace_part = f"{resource.namespace}:" if resource.namespace else ""
        return f"{resource.api_version}:{resource.kind}:{namespace_part}{resource.name}"

    def _record_lifecycle_events(
        self, changes: ChangeSet, repository_id: uuid.UUID, sync_run_id: uuid.UUID
    ):
        """Record all lifecycle events for trend analysis"""
        if not self.session:
            self.logger.warning(
                "No database session available, skipping lifecycle events recording"
            )
            return

        total_events = (
            len(changes.created) + len(changes.modified) + len(changes.deleted)
        )
        self.logger.debug(
            f"Recording {total_events} lifecycle events for sync_run_id: {sync_run_id}"
        )

        event_count = 0
        for change in changes.created + changes.modified + changes.deleted:
            event_count += 1
            self.logger.debug(
                f"Recording event {event_count}/{total_events}: "
                f"{change.type} for {change.resource_kind}/{change.resource_name} "
                f"in namespace {change.resource_namespace or 'default'} "
                f"at path {change.file_path}"
            )

            event = ResourceLifecycleEvent(
                resource_id=change.existing_resource.id
                if change.existing_resource
                else None,
                repository_id=repository_id,
                resource_name=change.resource_name,
                resource_namespace=change.resource_namespace,
                resource_kind=change.resource_kind,
                resource_api_version=change.resource_api_version,
                event_type=change.type,
                file_path=change.file_path,
                file_hash_before=change.file_hash_before,
                file_hash_after=change.file_hash_after,
                resource_snapshot=change.resource_data.to_dict()
                if change.resource_data
                else {},
                changes_detected=change.detailed_changes or [],
                sync_run_id=sync_run_id,
            )

            self.session.add(event)

        self.logger.debug(f"Added {event_count} lifecycle events to session")

    def _update_resources(self, changes: ChangeSet, repository_id: uuid.UUID):
        """Update resources in database based on detected changes"""
        if not self.session:
            self.logger.warning(
                "No database session available, skipping resource updates"
            )
            return

        self.logger.debug(
            f"Updating resources in database: "
            f"{len(changes.created)} to create, "
            f"{len(changes.modified)} to modify, "
            f"{len(changes.deleted)} to delete"
        )

        # Collect all resources and metrics for version resolution
        all_resources = {}
        metrics_map = {}

        # Handle created resources
        created_count = 0
        for change in changes.created:
            created_count += 1
            resource_key = change.resource_data.resource_key()
            self.logger.debug(
                f"Creating resource {created_count}/{len(changes.created)}: "
                f"{resource_key} at {change.resource_data.file_path}"
            )

            # Check if there's a deleted resource with the same unique constraint values
            # This handles the case where a resource was deleted and is now being re-added
            existing_deleted_resource = self.session.exec(
                select(KubernetesResource)
                .where(KubernetesResource.repository_id == repository_id)
                .where(
                    KubernetesResource.api_version == change.resource_data.api_version
                )
                .where(KubernetesResource.kind == change.resource_data.kind)
                .where(KubernetesResource.name == change.resource_data.name)
                .where(KubernetesResource.namespace == change.resource_data.namespace)
                .where(KubernetesResource.current_status == "DELETED")
            ).first()

            if existing_deleted_resource:
                # Resurrect the deleted resource instead of creating a new one
                self.logger.debug(
                    f"Resurrecting previously deleted resource: {resource_key}"
                )
                resource = existing_deleted_resource
                resource.file_path = change.resource_data.file_path
                resource.file_hash = change.resource_data.file_hash
                resource.resource_metadata = change.resource_data.metadata
                resource.spec = change.resource_data.spec
                resource.current_status = "ACTIVE"
                resource.deleted_at = None
                resource.modification_count += 1
                resource.last_change_type = "RESURRECTED"
                resource.last_updated_at = datetime.now(timezone.utc)
            else:
                # Create a new resource
                resource = KubernetesResource(
                    repository_id=repository_id,
                    api_version=change.resource_data.api_version,
                    kind=change.resource_data.kind,
                    name=change.resource_data.name,
                    namespace=change.resource_data.namespace,
                    file_path=change.resource_data.file_path,
                    file_hash=change.resource_data.file_hash,
                    resource_metadata=change.resource_data.metadata,
                    spec=change.resource_data.spec,
                    current_status="ACTIVE",
                    modification_count=0,
                    last_change_type="CREATED",
                )
                self.session.add(resource)

            # Create initial metrics record
            if self.resource_extractor:
                self.logger.debug(f"Extracting metrics for resource: {resource_key}")
                metrics = self.resource_extractor.extract_resource_metrics(
                    change.resource_data, resource
                )
                if metrics:
                    all_resources[resource_key] = change.resource_data
                    metrics_map[resource_key] = metrics
                    self.session.add(metrics)
                    self.logger.debug(f"Added metrics for resource: {resource_key}")
                else:
                    self.logger.debug(
                        f"No metrics extracted for resource: {resource_key}"
                    )

        # Handle modified resources
        modified_count = 0
        for change in changes.modified:
            modified_count += 1
            resource_key = change.resource_data.resource_key()
            self.logger.debug(
                f"Modifying resource {modified_count}/{len(changes.modified)}: "
                f"{resource_key} at {change.resource_data.file_path}"
            )

            resource = change.existing_resource
            resource.file_path = change.resource_data.file_path
            resource.file_hash = change.resource_data.file_hash
            resource.resource_metadata = change.resource_data.metadata
            resource.spec = change.resource_data.spec
            resource.modification_count += 1
            resource.last_change_type = "MODIFIED"
            resource.last_updated_at = datetime.now(timezone.utc)

            # Create new metrics record
            if self.resource_extractor:
                self.logger.debug(
                    f"Extracting metrics for modified resource: {resource_key}"
                )
                metrics = self.resource_extractor.extract_resource_metrics(
                    change.resource_data, resource
                )
                if metrics:
                    all_resources[resource_key] = change.resource_data
                    metrics_map[resource_key] = metrics
                    self.session.add(metrics)
                    self.logger.debug(
                        f"Added metrics for modified resource: {resource_key}"
                    )
                else:
                    self.logger.debug(
                        f"No metrics extracted for modified resource: {resource_key}"
                    )

        # Handle deleted resources
        deleted_count = 0
        for change in changes.deleted:
            deleted_count += 1
            resource_key = self._resource_key(change.existing_resource)
            self.logger.debug(
                f"Deleting resource {deleted_count}/{len(changes.deleted)}: {resource_key}"
            )

            resource = change.existing_resource
            resource.current_status = "DELETED"
            resource.deleted_at = datetime.now(timezone.utc)
            resource.last_change_type = "DELETED"
            resource.last_updated_at = datetime.now(timezone.utc)

        # Resolve cross-resource versions (e.g., HelmRelease getting version from OCIRepository)
        if self.resource_extractor and all_resources and metrics_map:
            self.logger.debug(
                f"Resolving cross-resource versions for {len(all_resources)} resources"
            )
            self.resource_extractor.resolve_cross_resource_versions(
                all_resources, metrics_map
            )
            self.logger.debug("Cross-resource version resolution completed")

        self.logger.debug("Committing database changes")
        self.session.commit()
        self.logger.info(
            f"Database update completed: "
            f"{len(changes.created)} created, "
            f"{len(changes.modified)} modified, "
            f"{len(changes.deleted)} deleted"
        )

    # Methods for testing compatibility
    def parse_yaml_content(self, content: str, file_path: str) -> ResourceData | None:
        """Parse YAML content and return resource data if valid"""
        self.logger.debug(f"Parsing YAML content from file: {file_path}")
        result = self.parser.parse_yaml_content(content, file_path)
        if result:
            self.logger.debug(f"Successfully parsed resource: {result.resource_key()}")
        else:
            self.logger.debug(f"No valid resource found in file: {file_path}")
        return result

    def parse_multi_document_yaml(
        self, content: str, file_path: str
    ) -> list[ResourceData]:
        """Parse multi-document YAML and return all valid resources"""
        self.logger.debug(f"Parsing multi-document YAML from file: {file_path}")
        results = self.parser.parse_multi_document_yaml(content, file_path)
        self.logger.debug(
            f"Found {len(results)} valid resources in multi-document YAML: {file_path}"
        )
        return results

    def is_target_resource(self, api_version: str, kind: str) -> bool:
        """Check if a resource type is one we want to track"""
        is_target = self.parser.is_target_resource(api_version, kind)
        self.logger.debug(f"Resource {api_version}/{kind} is target: {is_target}")
        return is_target

    def extract_references(self, resource_data: ResourceData) -> list:
        """Extract references from a resource for testing"""
        if not self.resource_extractor:
            self.logger.debug(
                "No resource extractor available for reference extraction"
            )
            return []

        references = self.resource_extractor.extract_references(resource_data)
        self.logger.debug(
            f"Extracted {len(references)} references from resource: {resource_data.resource_key()}"
        )
        return references
