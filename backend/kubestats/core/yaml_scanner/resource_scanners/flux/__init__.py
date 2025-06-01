from typing import Any, Dict, List, Set, Tuple
from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

from .helm_release import HelmReleaseResourceScanner
from .git_repository import GitRepositoryResourceScanner
from .kustomization import KustomizationResourceScanner
from .oci_repository import OciRepositoryResourceScanner


class FluxResourceScanner(ResourceScanner):
    """Scanner for Flux CD resources"""

    @property
    def scanners(self) -> Set[Tuple[str, str]]:
        return [
            HelmReleaseResourceScanner(),
            GitRepositoryResourceScanner(),
            KustomizationResourceScanner(),
            OciRepositoryResourceScanner(),
        ]

    @property
    def resource_types(self) -> Set[Tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        resource_types = set()
        for scanner in self.scanners:
            resource_types.update(scanner.resource_types)
        return resource_types
    
    def parse_document(self, filepath: str, document: Dict[str, Any]) -> ResourceData:
        """Parse a Flux resource document and return ResourceData"""
        for scanner in self.scanners:
            if scanner.is_supported_resource(
                document.get("apiVersion"), document.get("kind")
            ):
                return scanner.parse_document(filepath, document)

    def is_supported_resource(
        self, api_version: str, kind: str
    ) -> ResourceScanner | None:
        """Check if this is a Flux resource with version-agnostic matching"""
        for scanner in self.scanners:
            if scanner.is_supported_resource(api_version, kind):
                return scanner

    def extract_additional_data(self, document: Dict[str, Any]) -> dict:
        """Extract additional data for Flux resources"""
        return {}

    def post_process(self, resources: List[ResourceData]):
        path_ns_map = {}
        oci_versions = {}
        for resource in resources:
            if (
                resource.api_version.startswith("kustomize.toolkit.fluxcd.io")
                and resource.kind == "Kustomization"
            ):
                path_ns_map[resource.file_path] = resource.data.get("targetNamespace")
            if (
                resource.api_version.startswith("source.toolkit.fluxcd.io")
                and resource.kind == "OCIRepository"
            ):
                oci_versions[resource.name] = resource.version

        for resource in resources:
            if resource.namespace is None:
                for path, namespace in path_ns_map.items():
                    if resource.file_path.is_relative_to(path):
                        resource.namespace = namespace
                        break
            if (
                resource.version is None
                and resource.api_version.startswith("helm.toolkit.fluxcd.io")
                and resource.kind == "HelmRelease"
            ):
                resource.version = oci_versions.get(
                    resource.data.get("chartRef", {}).get("name"),
                )

        for scanner in self.scanners:
            scanner.post_process(resources)
