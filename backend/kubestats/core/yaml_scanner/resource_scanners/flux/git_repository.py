import logging

from typing import Any, Dict, Set, Tuple
from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

log = logging.getLogger(__name__)


class GitRepositoryResourceScanner(ResourceScanner):
    """Scanner for GitRepository resources in Flux CD"""

    @property
    def resource_types(self) -> Set[Tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        return {("source.toolkit.fluxcd.io", "GitRepository")}
