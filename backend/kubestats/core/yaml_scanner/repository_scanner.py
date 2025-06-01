"""
Repository scanner service for finding and parsing YAML files in Git repositories.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from kubestats.core.yaml_scanner.models import ResourceData
from kubestats.core.yaml_scanner.resource_scanners.flux import FluxResourceScanner

logger = logging.getLogger(__name__)


class RepositoryScanner:
    """Scans repository directories for YAML files and parses Flux resources."""

    def __init__(self):
        self.flux_scanner = FluxResourceScanner()

    def scan_directory(self, repo_path: Path) -> List[ResourceData]:
        """
        Scan a repository directory for YAML files and extract Flux resources.
        
        Args:
            repo_path: Path to the repository root directory
            
        Returns:
            List of ResourceData objects found in the repository
        """
        logger.info(f"Starting directory scan for repository at {repo_path}")
        
        resources = []
        yaml_files = self.find_yaml_files(repo_path)
        
        logger.info(f"Found {len(yaml_files)} YAML files to process")
        
        for file_path in yaml_files:
            try:
                file_resources = self.process_yaml_file(file_path, repo_path)
                resources.extend(file_resources)
            except Exception as e:
                logger.warning(f"Skipping corrupted YAML file {file_path}: {str(e)}")
                continue
        
        # Post-process resources for cross-resource relationships
        if resources:
            self.flux_scanner.post_process(resources)
        
        logger.info(f"Scan completed. Found {len(resources)} Flux resources")
        return resources

    def find_yaml_files(self, repo_path: Path) -> List[Path]:
        """
        Recursively find all YAML files in the repository.
        
        Args:
            repo_path: Path to the repository root directory
            
        Returns:
            List of Path objects for YAML files
        """
        yaml_files = []
        
        # Look for .yaml and .yml files recursively
        for pattern in ["**/*.yaml", "**/*.yml"]:
            yaml_files.extend(repo_path.glob(pattern))
        
        # Filter out hidden files and directories
        yaml_files = [
            f for f in yaml_files 
            if not any(part.startswith('.') for part in f.parts)
        ]
        
        return sorted(yaml_files)

    def parse_yaml_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse a YAML file and return all documents.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            List of parsed YAML documents
            
        Raises:
            yaml.YAMLError: If the file contains invalid YAML
            FileNotFoundError: If the file doesn't exist
            UnicodeDecodeError: If the file isn't valid UTF-8
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Handle empty files
            if not content.strip():
                return []
                
            # Parse all documents in the file (handle multi-document YAML)
            documents = list(yaml.safe_load_all(content))
            
            # Filter out None/empty documents
            documents = [doc for doc in documents if doc is not None]
            
            return documents
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML syntax in {file_path}: {str(e)}")
        except UnicodeDecodeError as e:
            raise UnicodeDecodeError(
                e.encoding, e.object, e.start, e.end,
                f"Invalid UTF-8 encoding in {file_path}: {e.reason}"
            )

    def process_yaml_file(self, file_path: Path, repo_root: Path) -> List[ResourceData]:
        """
        Process a single YAML file and extract Flux resources.
        
        Args:
            file_path: Path to the YAML file
            repo_root: Path to the repository root (for relative path calculation)
            
        Returns:
            List of ResourceData objects found in the file
        """
        documents = self.parse_yaml_file(file_path)
        resources = []
        
        # Calculate relative path from repository root
        relative_path = str(file_path.relative_to(repo_root))
        
        for doc_index, document in enumerate(documents):
            try:
                resource_data = self.process_document(relative_path, document, doc_index)
                if resource_data:
                    resources.append(resource_data)
            except Exception as e:
                logger.warning(
                    f"Skipping document {doc_index} in {relative_path}: {str(e)}"
                )
                continue
        
        return resources

    def process_document(
        self, 
        relative_path: str, 
        document: Dict[str, Any], 
        doc_index: int = 0
    ) -> ResourceData | None:
        """
        Process a single YAML document using FluxResourceScanner.
        
        Args:
            relative_path: Relative path to the file from repository root
            document: Parsed YAML document
            doc_index: Index of the document within the file (for multi-doc files)
            
        Returns:
            ResourceData object if the document is a supported Flux resource, None otherwise
        """
        # Skip if not a valid Kubernetes resource
        if not isinstance(document, dict):
            return None
            
        api_version = document.get("apiVersion")
        kind = document.get("kind")
        
        if not api_version or not kind:
            return None
        
        # Use FluxResourceScanner to check if this is a supported resource
        if not self.flux_scanner.is_supported_resource(api_version, kind):
            return None
        
        # Create file path identifier for multi-document files
        file_identifier = relative_path
        if doc_index > 0:
            file_identifier = f"{relative_path}#{doc_index}"
        
        # Parse the document using FluxResourceScanner
        try:
            resource_data = self.flux_scanner.parse_document(file_identifier, document)
            
            # Validate the resource data
            if not self._validate_resource_data(resource_data):
                logger.warning(
                    f"Invalid resource data in {file_identifier}: missing required fields"
                )
                return None
                
            return resource_data
            
        except Exception as e:
            logger.error(f"Error parsing Flux resource in {file_identifier}: {str(e)}")
            return None

    def _validate_resource_data(self, resource_data: ResourceData) -> bool:
        """
        Validate that ResourceData has all required fields.
        
        Args:
            resource_data: ResourceData object to validate
            
        Returns:
            True if valid, False otherwise
        """
        return (
            resource_data.api_version and
            resource_data.kind and
            resource_data.name and
            resource_data.file_path and
            resource_data.file_hash
        )
