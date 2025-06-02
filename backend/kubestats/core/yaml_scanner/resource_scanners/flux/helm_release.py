import logging
from typing import Any

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

log = logging.getLogger(__name__)


class HelmReleaseResourceScanner(ResourceScanner):
    """Scanner for HelmRelease resources in Flux CD"""

    @property
    def resource_types(self) -> set[tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        return {("helm.toolkit.fluxcd.io/v2", "HelmRelease")}

    def parse_document(self, filepath: str, document: dict[str, Any]) -> ResourceData:
        resource = super().parse_document(filepath, document)
        resource.version = (
            document.get("spec", {}).get("chart", {}).get("spec", {}).get("version")
        )
        return resource

    def post_process(self, resources: list[ResourceData]) -> None:
        """Post-process HelmRelease resources"""
        pass
