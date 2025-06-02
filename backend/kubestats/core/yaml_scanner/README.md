# YAML Scanner for Flux Resources

This module provides comprehensive scanning capabilities for Kubernetes repositories containing Flux CD resources. It can scan repository file paths, parse YAML documents with the FluxResourceScanner, and save ResourceData to the database with change tracking.

## Architecture Overview

```
Repository Scan Task
       ↓
Repository Scanner  ← finds YAML files, parses with FluxResourceScanner
       ↓
Resource Database Service  ← manages database operations & change tracking
       ↓
Database (KubernetesResource, ResourceLifecycleEvent)
```

## Components

### 1. RepositoryScanner
**File:** `repository_scanner.py`

Handles file system scanning and YAML parsing:
- Recursively scans directories for `.yaml` and `.yml` files
- Filters out hidden files/directories (starting with `.`)
- Parses YAML files with multi-document support
- Uses FluxResourceScanner to identify and parse supported Flux resources
- Skips corrupted files without failing entire scan

**Key Methods:**
- `scan_directory(repo_path)` - Main entry point for scanning
- `find_yaml_files(repo_path)` - Discovers YAML files recursively
- `process_yaml_file(file_path, repo_root)` - Processes individual files
- `process_document(relative_path, document)` - Handles single YAML documents

### 2. ResourceDatabaseService
**File:** `resource_db_service.py`

Manages database operations for scanned resources:
- Clean up existing resources for a repository
- Create new KubernetesResource records from ResourceData
- Generate ResourceLifecycleEvent records for change tracking
- Transaction management and rollback capabilities

**Key Methods:**
- `apply_scan_results(session, repository_id, resources)` - Main orchestration method
- `cleanup_existing_resources(session, repository_id)` - Removes old data
- `create_resources_from_scan(session, repository_id, resources)` - Creates new records
- `create_lifecycle_events(session, repository_id, resources, sync_run_id)` - Tracks changes

### 3. Enhanced Scanning Task
**File:** `../../../tasks/scan_repositories.py`

Updated `perform_yaml_scan` function that:
- Initializes scanner services
- Orchestrates the scanning process
- Updates repository status and metrics
- Triggers follow-up tasks

## Database Schema Integration

### KubernetesResource Table
The scanner creates records with:
- Repository linkage via `repository_id`
- Resource identification (api_version, kind, name, namespace)
- File tracking (file_path, file_hash)
- Content storage (resource_metadata, spec)
- Lifecycle tracking (status, change counts, timestamps)

### ResourceLifecycleEvent Table
Change events are created for:
- All new resources (`CREATED` events)
- Track file hashes and content snapshots
- Link to sync runs for batch operations
- Enable historical analysis and trending

## Usage

### Running a Repository Scan

```python
from kubestats.tasks.scan_repositories import scan_repository

# Trigger scan via Celery task
result = scan_repository.delay("repository-uuid-string")

# Or call directly (for testing)
from sqlmodel import Session
from kubestats.core.db import engine
from pathlib import Path

with Session(engine) as session:
    repository = get_repository_by_id(session, repository_id)
    repo_workdir = Path(repository.working_directory_path)
    scan_result = perform_yaml_scan(session, repository, repo_workdir)
```

### Accessing Scan Results

```python
from kubestats.crud import get_kubernetes_resources_by_repository

# Get resources for a repository
resources = get_kubernetes_resources_by_repository(
    session=session, 
    repository_id=repo_id,
    skip=0, 
    limit=100
)

# Get resource statistics
stats = get_kubernetes_resources_stats(
    session=session,
    repository_id=repo_id
)
```

## Supported Flux Resources

The FluxResourceScanner currently supports:
- **HelmRelease** (`helm.toolkit.fluxcd.io`)
- **GitRepository** (`source.toolkit.fluxcd.io`)
- **Kustomization** (`kustomize.toolkit.fluxcd.io`)
- **OCIRepository** (`source.toolkit.fluxcd.io`)

## Error Handling

### File-Level Errors
- Corrupted YAML files are skipped with warning logs
- Parse errors don't fail the entire scan
- UTF-8 encoding issues are handled gracefully

### Database Errors
- Full transaction rollback on database failures
- Repository scan status updated to ERROR
- Celery task retry mechanism with exponential backoff

### Resource Validation
- Invalid ResourceData objects are skipped
- Missing required fields logged as warnings
- FluxResourceScanner validation applied

## Configuration

### File Filtering
- Scans all directories recursively
- Includes all `.yaml` and `.yml` files
- Excludes hidden files/directories (starting with `.`)

### Resource Scope
- Only processes Flux CD resources (as determined by FluxResourceScanner)
- Skips standard Kubernetes resources not handled by Flux scanners
- Multi-document YAML files fully supported

### Performance
- No pagination for database operations (clean scan approach)
- Bulk operations for efficiency
- Single transaction per repository scan

## Monitoring and Logging

### Log Levels
- **INFO**: Scan progress, resource counts, timing
- **WARNING**: Skipped files, validation failures
- **ERROR**: Database errors, system failures

### Key Metrics
- Scan duration
- Resource counts (created/deleted/total)
- File processing statistics
- Error rates

### Example Log Output
```
INFO - Starting directory scan for repository at /path/to/repo
INFO - Found 15 YAML files to process
WARNING - Skipping corrupted YAML file bad-file.yaml: Invalid YAML syntax
INFO - Scan completed. Found 8 Flux resources
INFO - Cleaning up 5 existing resources for repository uuid
INFO - Creating 8 new resources in database
INFO - Successfully created 8 lifecycle events
INFO - Scan completed successfully: 8 created, 5 deleted, 8 total resources, 2.34s duration
```

## Future Enhancements

### Planned Features
1. **Incremental Scanning**: Compare with existing resources for true change detection
2. **Resource References**: Parse and track cross-resource dependencies
3. **Version Tracking**: Enhanced version detection for HelmReleases
4. **Metrics Collection**: Resource-specific metrics and health data
5. **Validation Rules**: Custom validation for Flux resource configurations

### Extensibility
- Additional resource scanners can be added to FluxResourceScanner
- Database service can be extended for other resource types
- Repository scanner supports pluggable file filters
- Change detection can be enhanced with detailed diff analysis
