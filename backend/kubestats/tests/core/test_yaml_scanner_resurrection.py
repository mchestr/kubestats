"""
Tests for YAML scanner resource resurrection functionality
"""

from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from kubestats.core.yaml_scanner import YAMLScanner
from kubestats.models import KubernetesResource, Repository, SyncStatus


def test_resource_resurrection_after_deletion(db: Session, tmp_path: Path):
    """Test that a resource can be resurrected after being deleted."""
    # Create test repository
    repository = Repository(
        name="test-repo",
        full_name="owner/test-repo",
        owner="owner",
        github_id=987654321,  # Use unique ID
        created_at=datetime.now(timezone.utc),
        sync_status=SyncStatus.SUCCESS,
        working_directory_path=str(tmp_path),
    )
    db.add(repository)
    db.commit()

    # Create the working directory with a test YAML file
    test_yaml = """---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: test-app
  namespace: default
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: test-chart
"""

    test_file = tmp_path / "test-app.yaml"
    test_file.write_text(test_yaml)

    # First scan - create the resource
    scanner = YAMLScanner(db)
    scan_result_1 = scanner.scan_repository(repository, tmp_path)

    assert scan_result_1.created_count == 1
    assert scan_result_1.modified_count == 0
    assert scan_result_1.deleted_count == 0

    # Verify resource was created
    created_resource = db.exec(
        select(KubernetesResource)
        .where(KubernetesResource.repository_id == repository.id)
        .where(KubernetesResource.name == "test-app")
    ).first()

    assert created_resource is not None
    assert created_resource.current_status == "ACTIVE"
    assert created_resource.last_change_type == "CREATED"
    original_id = created_resource.id

    # Remove the file (simulating deletion)
    test_file.unlink()

    # Second scan - delete the resource
    scan_result_2 = scanner.scan_repository(repository, tmp_path)

    assert scan_result_2.created_count == 0
    assert scan_result_2.modified_count == 0
    assert scan_result_2.deleted_count == 1

    # Verify resource was marked as deleted
    db.refresh(created_resource)
    assert created_resource.current_status == "DELETED"
    assert created_resource.last_change_type == "DELETED"
    assert created_resource.deleted_at is not None

    # Re-create the file (simulating re-addition)
    test_file.write_text(test_yaml)

    # Third scan - resurrect the resource
    scan_result_3 = scanner.scan_repository(repository, tmp_path)

    assert scan_result_3.created_count == 1
    assert scan_result_3.modified_count == 0
    assert scan_result_3.deleted_count == 0

    # Verify the same resource was resurrected (same ID)
    db.refresh(created_resource)
    assert created_resource.id == original_id  # Same resource, not a new one
    assert created_resource.current_status == "ACTIVE"
    assert created_resource.last_change_type == "RESURRECTED"
    assert created_resource.deleted_at is None
    assert created_resource.modification_count == 1  # Should have incremented


def test_resource_resurrection_with_modified_content(db: Session, tmp_path: Path):
    """Test that a resurrected resource has its content updated if it changed."""  # Create test repository
    repository = Repository(
        name="test-repo",
        full_name="owner/test-repo",
        owner="owner",
        github_id=987654322,  # Use unique ID
        created_at=datetime.now(timezone.utc),
        sync_status=SyncStatus.SUCCESS,
        working_directory_path=str(tmp_path),
    )
    db.add(repository)
    db.commit()

    # Original YAML content
    original_yaml = """---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: test-app
  namespace: default
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: test-chart
"""

    # Modified YAML content (different spec)
    modified_yaml = """---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: test-app
  namespace: default
spec:
  interval: 2h
  chartRef:
    kind: OCIRepository
    name: test-chart-v2
"""

    test_file = tmp_path / "test-app.yaml"

    # Create, delete, then recreate with different content
    test_file.write_text(original_yaml)
    scanner = YAMLScanner(db)

    # First scan - create
    scanner.scan_repository(repository, tmp_path)
    created_resource = db.exec(
        select(KubernetesResource)
        .where(KubernetesResource.repository_id == repository.id)
        .where(KubernetesResource.name == "test-app")
    ).first()
    original_spec = created_resource.spec

    # Delete
    test_file.unlink()
    scanner.scan_repository(repository, tmp_path)

    # Recreate with modified content
    test_file.write_text(modified_yaml)
    scan_result = scanner.scan_repository(repository, tmp_path)

    assert scan_result.created_count == 1

    # Verify content was updated
    db.refresh(created_resource)
    assert created_resource.current_status == "ACTIVE"
    assert created_resource.last_change_type == "RESURRECTED"
    assert created_resource.spec != original_spec
    assert created_resource.spec["interval"] == "2h"
    assert created_resource.spec["chartRef"]["name"] == "test-chart-v2"


def test_no_resurrection_when_no_deleted_resource_exists(db: Session, tmp_path: Path):
    """Test that normal creation works when no deleted resource exists."""
    # Create test repository
    repository = Repository(
        name="test-repo",
        full_name="owner/test-repo",
        owner="owner",
        github_id=987654323,  # Use unique ID
        created_at=datetime.now(timezone.utc),
        sync_status=SyncStatus.SUCCESS,
        working_directory_path=str(tmp_path),
    )
    db.add(repository)
    db.commit()

    # Create YAML file
    test_yaml = """---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: new-app
  namespace: default
spec:
  interval: 1h
"""

    test_file = tmp_path / "new-app.yaml"
    test_file.write_text(test_yaml)

    # Scan - should create normally
    scanner = YAMLScanner(db)
    scan_result = scanner.scan_repository(repository, tmp_path)

    assert scan_result.created_count == 1

    # Verify resource was created normally
    created_resource = db.exec(
        select(KubernetesResource)
        .where(KubernetesResource.repository_id == repository.id)
        .where(KubernetesResource.name == "new-app")
    ).first()

    assert created_resource is not None
    assert created_resource.current_status == "ACTIVE"
    assert created_resource.last_change_type == "CREATED"  # Not RESURRECTED
    assert created_resource.modification_count == 0
    assert created_resource.deleted_at is None
