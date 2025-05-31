"""
Resource metrics and reference extraction logic
"""

import uuid
from typing import Any

from sqlmodel import Session, select

from kubestats.models import (
    KubernetesResource,
    KubernetesResourceMetrics,
    KubernetesResourceReference,
)

from .models import ResourceData


class ResourceExtractor:
    """Extracts metrics and references from Kubernetes resources"""

    def __init__(self, session: Session):
        self.session = session

    def extract_resource_metrics(
        self, resource_data: ResourceData, resource: KubernetesResource
    ) -> KubernetesResourceMetrics | None:
        """Extract metrics from resource data"""

        metrics = KubernetesResourceMetrics(
            resource_id=resource.id, image_versions={}, reference_versions={}
        )

        # Extract HelmRelease specific metrics
        if resource_data.kind == "HelmRelease":
            spec = resource_data.spec

            # Pattern 1: chartRef (OCIRepository reference)
            if "chartRef" in spec:
                chart_ref = spec["chartRef"]
                metrics.chart_name = chart_ref.get("name")
                # Version will be resolved from referenced OCIRepository later
                # Store reference info for version resolution
                metrics.source_revision = chart_ref.get("name")

            # Pattern 2: chart.spec (HelmRepository reference)
            elif "chart" in spec:
                chart = spec["chart"]
                chart_spec = chart.get("spec", {})

                metrics.chart_name = chart_spec.get("chart")
                metrics.chart_version = chart_spec.get("version")

                # Extract chart repository from sourceRef
                source_ref = chart_spec.get("sourceRef", {})
                if source_ref.get("kind") == "OCIRepository":
                    metrics.chart_repository = f"oci://{source_ref.get('name')}"
                elif source_ref.get("kind") == "HelmRepository":
                    metrics.chart_repository = source_ref.get("name")

                # Extract source revision if available
                metrics.source_revision = source_ref.get("name")

        # Extract OCIRepository specific metrics
        elif resource_data.kind == "OCIRepository":
            spec = resource_data.spec
            ref = spec.get("ref", {})

            # Extract version from tag
            metrics.chart_version = ref.get("tag")

            # Extract repository URL
            metrics.chart_repository = spec.get("url")

        # Extract Deployment specific metrics
        elif resource_data.kind == "Deployment":
            spec = resource_data.spec
            metrics.replicas = spec.get("replicas")

            # Extract image versions from containers
            template = spec.get("template", {})
            pod_spec = template.get("spec", {})
            containers = pod_spec.get("containers", [])

            for container in containers:
                container_name = container.get("name")
                image = container.get("image")
                if container_name and image:
                    metrics.image_versions[container_name] = image

        return metrics

    def resolve_cross_resource_versions(
        self,
        resources: dict[str, ResourceData],
        metrics_map: dict[str, KubernetesResourceMetrics],
    ) -> None:
        """Resolve versions from referenced resources (e.g., OCIRepository -> HelmRelease)"""

        for resource_data in resources.values():
            if resource_data.kind == "HelmRelease":
                resource_key = resource_data.resource_key()
                if resource_key not in metrics_map:
                    continue

                metrics = metrics_map[resource_key]

                # Only resolve if HelmRelease uses chartRef and doesn't have a version yet
                if "chartRef" in resource_data.spec and not metrics.chart_version:
                    chart_ref = resource_data.spec["chartRef"]
                    target_name = chart_ref.get("name")
                    target_kind = chart_ref.get("kind", "OCIRepository")
                    target_namespace = chart_ref.get(
                        "namespace", resource_data.namespace
                    )

                    # Find the referenced resource
                    target_api_version = self._get_api_version_for_kind(target_kind)
                    namespace_part = f"{target_namespace}:" if target_namespace else ""
                    target_key = f"{target_api_version}:{target_kind}:{namespace_part}{target_name}"

                    if target_key in resources and target_key in metrics_map:
                        target_metrics = metrics_map[target_key]
                        if target_metrics.chart_version:
                            # Copy version from referenced resource
                            metrics.chart_version = target_metrics.chart_version
                            # Also copy repository URL if available
                            if (
                                target_metrics.chart_repository
                                and not metrics.chart_repository
                            ):
                                metrics.chart_repository = (
                                    target_metrics.chart_repository
                                )

    def extract_resource_references(
        self, resources: dict[str, ResourceData], repository_id: uuid.UUID
    ):
        """Extract and store resource references"""

        for resource_data in resources.values():
            refs = self.find_resource_references(resource_data)

            # Find the source resource ID
            source_resource_id = self._resolve_source_resource(
                resource_data, repository_id
            )

            for ref in refs:
                # Try to resolve target resource within the repository
                target_resource_id = self._resolve_reference_target(
                    ref, resources, repository_id
                )

                # Resolve version for chartRef references by looking up the referenced resource
                referenced_version = ref.get("version")
                if (
                    ref["type"] == "chartRef"
                    and not referenced_version
                    and ref["target_kind"] == "OCIRepository"
                ):
                    # Build target resource key to find the OCIRepository
                    namespace_part = (
                        f"{ref.get('target_namespace')}:"
                        if ref.get("target_namespace")
                        else ""
                    )
                    target_key = f"{ref.get('target_api_version')}:{ref['target_kind']}:{namespace_part}{ref['target_name']}"

                    # Look up the OCIRepository in the current scan
                    if target_key in resources:
                        target_resource_data = resources[target_key]
                        if target_resource_data.kind == "OCIRepository":
                            # Extract version from OCIRepository spec.ref.tag
                            oci_ref = target_resource_data.spec.get("ref", {})
                            referenced_version = oci_ref.get("tag")

                reference = KubernetesResourceReference(
                    source_resource_id=source_resource_id,
                    source_repository_id=repository_id,
                    target_repository_id=repository_id if target_resource_id else None,
                    target_resource_id=target_resource_id,
                    reference_type=ref["type"],
                    reference_path=ref["path"],
                    target_name=ref["target_name"],
                    target_namespace=ref.get("target_namespace"),
                    target_kind=ref["target_kind"],
                    target_api_version=ref.get("target_api_version"),
                    is_external_reference=target_resource_id is None,
                    referenced_version=referenced_version,
                )

                self.session.add(reference)

    def find_resource_references(
        self, resource_data: ResourceData
    ) -> list[dict[str, Any]]:
        """Find all references made by a resource"""
        references = []

        if resource_data.kind == "HelmRelease":
            spec = resource_data.spec

            # Pattern 1: chartRef (OCIRepository reference)
            if "chartRef" in spec:
                chart_ref = spec["chartRef"]
                references.append(
                    {
                        "type": "chartRef",
                        "path": "spec.chartRef",
                        "target_name": chart_ref.get("name", ""),
                        "target_namespace": chart_ref.get(
                            "namespace", resource_data.namespace
                        ),
                        "target_kind": chart_ref.get("kind", "OCIRepository"),
                        "target_api_version": self._get_api_version_for_kind(
                            chart_ref.get("kind", "OCIRepository")
                        ),
                    }
                )

            # Pattern 2: chart.spec.sourceRef (HelmRepository reference)
            elif "chart" in spec:
                chart = spec["chart"]
                chart_spec = chart.get("spec", {})
                source_ref = chart_spec.get("sourceRef", {})

                if source_ref:
                    references.append(
                        {
                            "type": "sourceRef",
                            "path": "spec.chart.spec.sourceRef",
                            "target_name": source_ref.get("name", ""),
                            "target_namespace": source_ref.get(
                                "namespace", resource_data.namespace
                            ),
                            "target_kind": source_ref.get("kind", "HelmRepository"),
                            "target_api_version": self._get_api_version_for_kind(
                                source_ref.get("kind", "HelmRepository")
                            ),
                            "version": chart_spec.get("version"),
                        }
                    )

        elif resource_data.kind == "Kustomization":
            # Extract source reference
            source_ref = resource_data.spec.get("sourceRef", {})
            if source_ref:
                references.append(
                    {
                        "type": "sourceRef",
                        "path": "spec.sourceRef",
                        "target_name": source_ref.get("name", ""),
                        "target_namespace": source_ref.get(
                            "namespace", resource_data.namespace
                        ),
                        "target_kind": source_ref.get("kind", "GitRepository"),
                        "target_api_version": "source.toolkit.fluxcd.io/v1beta2",
                    }
                )

        # TODO: Add more reference types (ConfigMap refs, Secret refs, etc.)

        return references

    def _resolve_reference_target(
        self,
        ref: dict[str, Any],
        resources: dict[str, ResourceData],
        repository_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Try to resolve a reference to an actual resource ID"""

        # Build target resource key
        namespace_part = (
            f"{ref.get('target_namespace')}:" if ref.get("target_namespace") else ""
        )
        target_key = f"{ref.get('target_api_version')}:{ref['target_kind']}:{namespace_part}{ref['target_name']}"

        # Check if target exists in current filesystem scan
        if target_key in resources:
            # Get existing resource ID from database
            existing = self.session.exec(
                select(KubernetesResource)
                .where(KubernetesResource.repository_id == repository_id)
                .where(KubernetesResource.api_version == ref.get("target_api_version"))
                .where(KubernetesResource.kind == ref["target_kind"])
                .where(KubernetesResource.name == ref["target_name"])
                .where(KubernetesResource.namespace == ref.get("target_namespace"))
                .where(KubernetesResource.current_status == "ACTIVE")
            ).first()

            return existing.id if existing else None

        return None

    def extract_references(self, resource_data: ResourceData) -> list:
        """Extract references from a resource for testing"""
        refs = self.find_resource_references(resource_data)

        # Convert to simple reference objects for testing
        reference_objects = []
        for ref in refs:
            # Create a simple object with the reference data
            ref_obj = type(
                "ReferenceData",
                (),
                {
                    "reference_type": ref["type"],
                    "target_kind": ref["target_kind"],
                    "target_name": ref["target_name"],
                    "target_namespace": ref.get("target_namespace"),
                    "target_api_version": ref.get("target_api_version"),
                    "referenced_version": ref.get("version"),
                },
            )()
            reference_objects.append(ref_obj)

        return reference_objects

    def _get_api_version_for_kind(self, kind: str) -> str:
        """Get the default API version for a given resource kind"""
        api_version_map = {
            "OCIRepository": "source.toolkit.fluxcd.io/v1",
            "HelmRepository": "source.toolkit.fluxcd.io/v1beta2",
            "GitRepository": "source.toolkit.fluxcd.io/v1beta2",
        }
        return api_version_map.get(kind, "source.toolkit.fluxcd.io/v1beta2")

    def _resolve_source_resource(
        self, resource_data: ResourceData, repository_id: uuid.UUID
    ) -> uuid.UUID | None:
        """Find the source resource ID in the database"""

        existing = self.session.exec(
            select(KubernetesResource)
            .where(KubernetesResource.repository_id == repository_id)
            .where(KubernetesResource.api_version == resource_data.api_version)
            .where(KubernetesResource.kind == resource_data.kind)
            .where(KubernetesResource.name == resource_data.name)
            .where(KubernetesResource.namespace == resource_data.namespace)
            .where(KubernetesResource.current_status == "ACTIVE")
        ).first()

        return existing.id if existing else None
