"""
YAML parser for extracting Kubernetes resources from files
"""

import hashlib
from pathlib import Path

import yaml

from .models import ResourceData


class YAMLParser:
    """Handles parsing of YAML files and extraction of Kubernetes resources"""

    # Target resource types we're interested in
    FLUX_RESOURCE_TYPES = {
        ("helm.toolkit.fluxcd.io/v2", "HelmRelease"),
        ("helm.toolkit.fluxcd.io/v2beta1", "HelmRelease"),
        ("helm.toolkit.fluxcd.io/v2beta2", "HelmRelease"),
        ("source.toolkit.fluxcd.io/v1beta2", "OCIRepository"),
        ("source.toolkit.fluxcd.io/v1beta1", "OCIRepository"),
        ("source.toolkit.fluxcd.io/v1", "OCIRepository"),
        ("source.toolkit.fluxcd.io/v1beta2", "GitRepository"),
        ("source.toolkit.fluxcd.io/v1beta1", "GitRepository"),
        ("kustomize.toolkit.fluxcd.io/v1", "Kustomization"),
        ("kustomize.toolkit.fluxcd.io/v1beta2", "Kustomization"),
    }

    KUBERNETES_RESOURCE_TYPES = {
        ("apps/v1", "Deployment"),
        ("apps/v1", "StatefulSet"),
        ("apps/v1", "DaemonSet"),
        ("apps/v1", "ReplicaSet"),
        ("v1", "Service"),
        ("v1", "ConfigMap"),
        ("v1", "Secret"),
        ("v1", "ServiceAccount"),
        ("networking.k8s.io/v1", "Ingress"),
        ("networking.k8s.io/v1", "NetworkPolicy"),
        ("gateway.networking.k8s.io/v1beta1", "HTTPRoute"),
        ("gateway.networking.k8s.io/v1alpha2", "HTTPRoute"),
        ("gateway.networking.k8s.io/v1", "HTTPRoute"),
        ("autoscaling/v2", "HorizontalPodAutoscaler"),
        ("policy/v1", "PodDisruptionBudget"),
        ("rbac.authorization.k8s.io/v1", "Role"),
        ("rbac.authorization.k8s.io/v1", "RoleBinding"),
        ("rbac.authorization.k8s.io/v1", "ClusterRole"),
        ("rbac.authorization.k8s.io/v1", "ClusterRoleBinding"),
    }

    def __init__(self):
        self.all_resource_types = (
            self.FLUX_RESOURCE_TYPES | self.KUBERNETES_RESOURCE_TYPES
        )

    def scan_filesystem(self, repo_path: Path) -> dict[str, ResourceData]:
        """Scan filesystem and extract all Kubernetes resources"""
        resources = {}

        # Find all YAML files
        yaml_files = list(repo_path.rglob("*.yaml")) + list(repo_path.rglob("*.yml"))

        for yaml_file in yaml_files:
            try:
                # Skip certain directories that typically don't contain manifests
                if any(
                    skip_dir in yaml_file.parts
                    for skip_dir in [".git", "node_modules", "vendor"]
                ):
                    continue

                # Read and parse YAML file
                with open(yaml_file, encoding="utf-8") as f:
                    content = f.read()

                # Skip empty files
                if not content.strip():
                    continue

                # Parse multi-document YAML files
                file_resources = self.parse_multi_document_yaml(
                    content, str(yaml_file.relative_to(repo_path))
                )

                # Add all resources to the collection
                for resource_data in file_resources:
                    resources[resource_data.resource_key()] = resource_data

            except Exception as e:
                # Log error but continue processing other files
                print(f"Error processing {yaml_file}: {e}")
                continue

        return resources

    def parse_yaml_content(self, content: str, file_path: str) -> ResourceData | None:
        """Parse YAML content and return resource data if valid"""
        try:
            # Calculate file hash
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Parse YAML
            try:
                doc = yaml.safe_load(content)
            except yaml.YAMLError:
                return None

            if not doc or not isinstance(doc, dict):
                return None

            # Check if document has required Kubernetes fields
            if not all(key in doc for key in ["apiVersion", "kind", "metadata"]):
                return None

            api_version = doc["apiVersion"]
            kind = doc["kind"]

            # Check if this is a resource type we care about
            if not self.is_target_resource(api_version, kind):
                return None

            metadata = doc.get("metadata", {})
            name = metadata.get("name")
            namespace = metadata.get("namespace")

            if not name:
                return None

            return ResourceData(
                api_version=api_version,
                kind=kind,
                name=name,
                namespace=namespace,
                file_path=file_path,
                file_hash=file_hash,
                metadata=metadata,
                spec=doc.get("spec", {}),
                raw_content=doc,
            )

        except Exception:
            return None

    def parse_multi_document_yaml(
        self, content: str, file_path: str
    ) -> list[ResourceData]:
        """Parse multi-document YAML and return all valid resources"""
        resources = []

        try:
            # Calculate file hash
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Parse YAML documents
            try:
                documents = list(yaml.safe_load_all(content))
            except yaml.YAMLError:
                return resources

            # Process each document
            for doc in documents:
                if not doc or not isinstance(doc, dict):
                    continue

                # Check if document has required Kubernetes fields
                if not all(key in doc for key in ["apiVersion", "kind", "metadata"]):
                    continue

                api_version = doc["apiVersion"]
                kind = doc["kind"]

                # Check if this is a resource type we care about
                if not self.is_target_resource(api_version, kind):
                    continue

                metadata = doc.get("metadata", {})
                name = metadata.get("name")
                namespace = metadata.get("namespace")

                if not name:
                    continue

                resource_data = ResourceData(
                    api_version=api_version,
                    kind=kind,
                    name=name,
                    namespace=namespace,
                    file_path=file_path,
                    file_hash=file_hash,
                    metadata=metadata,
                    spec=doc.get("spec", {}),
                    raw_content=doc,
                )

                resources.append(resource_data)

        except Exception:
            pass

        return resources

    def is_target_resource(self, api_version: str, kind: str) -> bool:
        """Check if a resource type is one we want to track"""
        return (api_version, kind) in self.all_resource_types
