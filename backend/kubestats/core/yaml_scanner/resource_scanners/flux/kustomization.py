import logging
from typing import Set, Tuple
from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

log = logging.getLogger(__name__)


class KustomizationResourceScanner(ResourceScanner):
    """Scanner for Kustomization resources in Flux CD"""

    @property
    def resource_types(self) -> Set[Tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        return {("kustomize.toolkit.fluxcd.io", "Kustomization")}

    def extract_additional_data(self, resource_data: ResourceData) -> dict:
        """Extract additional Kustomization-specific data"""
        log.info("Extracting additional data for Kustomization resource")
        return {}
