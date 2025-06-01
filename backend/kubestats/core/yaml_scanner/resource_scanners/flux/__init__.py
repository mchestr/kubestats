from pathlib import Path
from typing import Any

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

from .git_repository import GitRepositoryResourceScanner
from .helm_release import HelmReleaseResourceScanner
from .kustomization import KustomizationResourceScanner
from .oci_repository import OciRepositoryResourceScanner


class FluxResourceScanner(ResourceScanner):
    """Scanner for Flux CD resources"""

    @property
    def scanners(self) -> list[ResourceScanner]:
        return [
            HelmReleaseResourceScanner(),
            GitRepositoryResourceScanner(),
            KustomizationResourceScanner(),
            OciRepositoryResourceScanner(),
        ]

    @property
    def resource_types(self) -> set[tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        resource_types = set()
        for scanner in self.scanners:
            resource_types.update(scanner.resource_types)
        return resource_types

    def parse_document(self, filepath: str, document: dict[str, Any]) -> ResourceData:
        """Parse a Flux resource document and return ResourceData"""
        api_version = document.get("apiVersion")
        kind = document.get("kind")

        if not api_version or not kind:
            raise ValueError(
                f"Document missing required apiVersion or kind: {document}"
            )

        for scanner in self.scanners:
            if scanner.is_supported_resource(api_version, kind):
                return scanner.parse_document(filepath, document)
        raise ValueError(f"No scanner found for document: {api_version}/{kind}")

    def is_supported_resource(
        self, api_version: str, kind: str
    ) -> ResourceScanner | None:
        """Check if this is a Flux resource with version-agnostic matching"""
        for scanner in self.scanners:
            if scanner.is_supported_resource(api_version, kind):
                return scanner
        return None

    def extract_additional_data(self, document: dict[str, Any]) -> dict[str, Any]:
        """Extract additional data for Flux resources"""
        return {}

    def post_process(self, resources: list[ResourceData]) -> None:
        path_ns_map = {}
        oci_versions = {}
        for resource in resources:
            if (
                resource.api_version.startswith("kustomize.toolkit.fluxcd.io")
                and resource.kind == "Kustomization"
            ):
                if resource.data:
                    path_ns_map[Path(resource.file_path).parent] = resource.data.get(
                        "targetNamespace"
                    )
            if (
                resource.api_version.startswith("source.toolkit.fluxcd.io")
                and resource.kind == "OCIRepository"
            ):
                oci_versions[resource.name] = resource.version

        for resource in resources:
            if resource.namespace is None:
                for path, namespace in path_ns_map.items():
                    if Path(resource.file_path).is_relative_to(path):
                        resource.namespace = namespace
                        break
            if (
                resource.version is None
                and resource.api_version.startswith("helm.toolkit.fluxcd.io")
                and resource.kind == "HelmRelease"
                and resource.data
            ):
                resource.version = oci_versions.get(
                    resource.data.get("chartRef", {}).get("name"),
                )

        for scanner in self.scanners:
            scanner.post_process(resources)
