import logging

from kubestats.core.yaml_scanner.resource_scanners import ResourceScanner

log = logging.getLogger(__name__)


class GitRepositoryResourceScanner(ResourceScanner):
    """Scanner for GitRepository resources in Flux CD"""

    @property
    def resource_types(self) -> set[tuple[str, str]]:
        """Return the set of (api_version, kind) tuples this scanner handles"""
        return {("source.toolkit.fluxcd.io", "GitRepository")}
