from abc import ABC, abstractmethod
import hashlib
from typing import Any, Dict, List, Set, Tuple

from kubestats.core.yaml_scanner.models import ResourceData


class ResourceScanner(ABC):
    """Base class for resource-specific scanners"""

    @property
    @abstractmethod
    def resource_types(self) -> Set[Tuple[str, str]]:
        """Return the set of (api_version_prefix, kind) tuples this scanner handles"""
        pass

    def parse_document(self, filepath: str, document: Dict[str, Any]) -> ResourceData:
        """Parse a YAML document and return resource data"""
        return ResourceData(
            api_version=document.get("apiVersion"),
            kind=document.get("kind"),
            file_hash=hashlib.sha256(str(document).encode("utf-8")).hexdigest(),
            file_path=filepath,
            name=document.get("metadata", {}).get("name"),
            namespace=document.get("metadata", {}).get("namespace"),
            data=self.extract_additional_data(document),
        )

    def scan(self, filepath: str, document: Any) -> ResourceData | None:
        """Scan a YAML document and return resource data"""
        api_version = document.get("apiVersion")
        kind = document.get("kind")
        if not (api_version and kind) or not self.is_supported_resource(api_version, kind):
            return None
        return self.parse_document(filepath, document)

    def is_supported_resource(self, api_version: str, kind: str) -> "ResourceScanner | None":
        """Check if this scanner supports the given resource type"""
        for prefix, resource_kind in self.resource_types:
            if api_version.startswith(prefix) and kind == resource_kind:
                return self

    def post_process(self, resources: List[ResourceData]) -> None:
        """Post-process resources after scanning. Override in subclasses if needed."""
        pass

    def extract_additional_data(self, document: Dict[str, Any]) -> dict:
        """Extract additional data for Flux resources"""
        return document.get("spec", {})

    def validate_resource(self, resource_data: ResourceData) -> bool:
        """Validate resource-specific requirements. Override in subclasses if needed."""
        return True
        
