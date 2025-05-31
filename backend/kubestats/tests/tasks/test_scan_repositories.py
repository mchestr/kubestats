"""
Tests for repository scanning tasks.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from kubestats.models import Repository, SyncStatus
from kubestats.tasks.scan_repositories import (
    scan_repository,
)


def test_scan_single_repository_nonexistent(db: Session):
    """Test scanning non-existent repository."""
    fake_repo_id = str(uuid.uuid4())

    # Patch retry to not actually retry but re-raise the original exception
    with patch("kubestats.tasks.scan_repositories.scan_repository.retry") as mock_retry:
        mock_retry.side_effect = lambda *args, **kwargs: exec('raise kwargs["exc"]')

        with pytest.raises(ValueError, match="Repository .* not found"):
            scan_repository(fake_repo_id)


def test_scan_single_repository_no_working_directory(db: Session):
    """Test scanning repository without working directory."""
    repository = Repository(
        name="test-repo",
        full_name="owner/test-repo",
        owner="owner",
        github_id=987654330,  # Use unique ID
        created_at=datetime.now(timezone.utc),
        sync_status=SyncStatus.SUCCESS,
        working_directory_path=None,
    )
    db.add(repository)
    db.commit()

    # Patch retry to not actually retry but re-raise the original exception
    with patch("kubestats.tasks.scan_repositories.scan_repository.retry") as mock_retry:
        mock_retry.side_effect = lambda *args, **kwargs: exec('raise kwargs["exc"]')

        with pytest.raises(ValueError, match="has no working directory"):
            scan_repository(str(repository.id))


def test_scan_single_repository_success(db: Session, tmp_path: Path):
    """Test successful repository scanning."""
    # Create test repository with working directory
    repository = Repository(
        name="test-repo",
        full_name="owner/test-repo",
        owner="owner",
        github_id=987654331,  # Use unique ID
        created_at=datetime.now(timezone.utc),
        sync_status=SyncStatus.SUCCESS,
        working_directory_path=str(tmp_path / "test-repo"),
        scan_status=SyncStatus.PENDING,
    )
    db.add(repository)
    db.commit()

    # Create the working directory
    workdir = Path(repository.working_directory_path)
    workdir.mkdir(parents=True, exist_ok=True)

    # Mock the YAML scanner
    mock_scan_result = Mock()
    mock_scan_result.total_resources = 5
    mock_scan_result.created_count = 2
    mock_scan_result.modified_count = 1
    mock_scan_result.deleted_count = 0
    mock_scan_result.scan_duration_seconds = 1.5

    # Mock GitHub stats that would be passed from sync task
    github_stats = {
        "stars_count": 10,
        "forks_count": 3,
        "watchers_count": 8,
        "open_issues_count": 2,
        "size": 512,
        "updated_at": "2024-01-15T10:30:00Z",
        "pushed_at": "2024-01-14T14:20:00Z",
    }

    with patch("kubestats.tasks.scan_repositories.YAMLScanner") as mock_scanner_class:
        with patch(
            "kubestats.tasks.save_repository_metrics.save_repository_metrics.delay"
        ) as mock_metrics_delay:
            mock_scanner = Mock()
            mock_scanner_class.return_value = mock_scanner
            mock_scanner.scan_repository.return_value = mock_scan_result

            # Mock the metrics task
            mock_task = Mock()
            mock_task.id = "mock-task-id"
            mock_metrics_delay.return_value = mock_task

            result = scan_repository(str(repository.id), github_stats)

            # Verify result
            assert result["status"] == "success"
            assert result["repository_id"] == str(repository.id)
            assert result["repository_name"] == "owner/test-repo"
            assert result["scan_result"]["total_resources"] == 5
            assert result["scan_result"]["created_count"] == 2

            # Verify repository status was updated
            db.refresh(repository)
            assert repository.scan_status == SyncStatus.SUCCESS
            assert repository.last_scan_at is not None
            assert repository.scan_error is None
            assert repository.last_scan_total_resources == 5

            # Verify metrics task was triggered with GitHub stats
            mock_metrics_delay.assert_called_once_with(
                str(repository.id), 5, github_stats
            )


def test_scan_single_repository_scan_error(db: Session, tmp_path: Path):
    """Test repository scanning with YAML scanner error."""
    # Create test repository
    repository = Repository(
        name="test-repo",
        full_name="owner/test-repo",
        owner="owner",
        github_id=987654332,  # Use unique ID
        created_at=datetime.now(timezone.utc),
        sync_status=SyncStatus.SUCCESS,
        working_directory_path=str(tmp_path / "test-repo"),
        scan_status=SyncStatus.PENDING,
    )
    db.add(repository)
    db.commit()

    # Create the working directory
    workdir = Path(repository.working_directory_path)
    workdir.mkdir(parents=True, exist_ok=True)

    # Mock the YAML scanner to raise an error
    with patch("kubestats.tasks.scan_repositories.YAMLScanner") as mock_scanner_class:
        mock_scanner = Mock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_repository.side_effect = Exception("Scan failed")

        with pytest.raises(Exception):  # noqa: B017
            with patch(
                "kubestats.tasks.scan_repositories.scan_repository.retry"
            ) as mock_retry:
                mock_retry.side_effect = Exception("Retry called")
                scan_repository(str(repository.id))

        # Verify repository error status was updated
        db.refresh(repository)
        assert repository.scan_status == SyncStatus.ERROR
        assert repository.scan_error == "Scan failed"
