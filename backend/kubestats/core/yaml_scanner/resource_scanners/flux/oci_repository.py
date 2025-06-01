import logging
from typing import Set, Tuple
from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

log = logging.getLogger(__name__)


class OciRepositoryResourceScanner(ResourceScanner):
    """Scanner for OCIRepository resources in Flux CD"""

    @property
    def resource_types(self) -> Set[Tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        return {("source.toolkit.fluxcd.io", "OCIRepository")}

    def parse_document(self, filepath, document):
        resource = super().parse_document(filepath, document)
        resource.version = document.get("spec", {}).get("ref", {}).get("tag")
        return resource
