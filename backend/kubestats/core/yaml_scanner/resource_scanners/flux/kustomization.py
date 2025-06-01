import logging

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

log = logging.getLogger(__name__)


class KustomizationResourceScanner(ResourceScanner):
    """Scanner for Kustomization resources in Flux CD"""

    @property
    def resource_types(self) -> set[tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        return {("kustomize.toolkit.fluxcd.io", "Kustomization")}

    def post_process(self, resources: list[ResourceData]) -> None:
        """Post-process Kustomization resources"""
        pass
