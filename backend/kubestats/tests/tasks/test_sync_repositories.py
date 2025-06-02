"""
Tests for repository sync tasks.
"""

import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlmodel import Session

from kubestats.models import Repository, SyncStatus
from kubestats.tasks.sync_repositories import (
    cleanup_repository_workdirs,
    sync_repository,
)


@patch("kubestats.tasks.sync_repositories.settings")
@patch("kubestats.tasks.sync_repositories.git.Repo")
@patch("kubestats.tasks.scan_repositories.scan_repository.delay")
def test_sync_single_repository_clone_new(
    mock_scan_delay: Mock,
    mock_git_repo: Mock,
    mock_settings: Mock,
    db: Session,
    sample_repository: Repository,
) -> None:
    """Test syncing a repository that needs to be cloned."""
    # Setup temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir
        repo_workdir = Path(temp_dir) / str(sample_repository.id)

        # Mock git operations
        mock_repo = MagicMock()
        mock_git_repo.clone_from.return_value = mock_repo

        # Mock scan task
        mock_task = Mock()
        mock_task.id = "scan-task-id"
        mock_scan_delay.return_value = mock_task

        # Add repository to session
        db.add(sample_repository)
        db.commit()

        # Test with provided GitHub stats
        github_stats = {
            "stars_count": 25,
            "forks_count": 5,
            "watchers_count": 20,
            "open_issues_count": 3,
            "size": 1024,
            "updated_at": "2024-01-15T10:30:00Z",
            "pushed_at": "2024-01-14T14:20:00Z",
        }

        result = sync_repository(str(sample_repository.id), github_stats)

        # Verify result
        assert result["status"] == "success"
        assert result["action"] == "cloned"
        assert result["repository_name"] == sample_repository.full_name

        # Verify git operations
        mock_git_repo.clone_from.assert_called_once_with(
            f"https://github.com/{sample_repository.full_name}.git",
            repo_workdir,
            branch=sample_repository.default_branch,
            depth=1,
        )

        # Verify scan task was triggered with GitHub stats
        mock_scan_delay.assert_called_once_with(str(sample_repository.id), github_stats)

        # Verify database updates
        db.refresh(sample_repository)
        assert sample_repository.sync_status == SyncStatus.SUCCESS
        assert sample_repository.last_sync_at is not None
        assert sample_repository.working_directory_path == str(repo_workdir)
        assert sample_repository.sync_error is None


@patch("kubestats.tasks.sync_repositories.settings")
@patch("kubestats.tasks.sync_repositories.git.Repo")
@patch("kubestats.tasks.scan_repositories.scan_repository.delay")
def test_sync_single_repository_update_existing(
    mock_scan_delay: Mock,
    mock_git_repo_class: Mock,
    mock_settings: Mock,
    db: Session,
    sample_repository: Repository,
) -> None:
    """Test syncing a repository that already exists."""
    # Setup temporary directory with existing git repo
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir
        repo_workdir = Path(temp_dir) / str(sample_repository.id)
        repo_workdir.mkdir(parents=True)
        git_dir = repo_workdir / ".git"
        git_dir.mkdir()

        # Mock git operations
        mock_repo = MagicMock()
        mock_origin = MagicMock()
        mock_repo.remotes.origin = mock_origin
        mock_git_repo_class.return_value = mock_repo

        # Mock scan task
        mock_task = Mock()
        mock_task.id = "scan-task-id"
        mock_scan_delay.return_value = mock_task

        # Add repository to session
        db.add(sample_repository)
        db.commit()

        # Test with provided GitHub stats
        github_stats = {
            "stars_count": 15,
            "forks_count": 3,
            "watchers_count": 12,
            "open_issues_count": 2,
            "size": 512,
            "updated_at": "2024-01-10T09:00:00Z",
            "pushed_at": "2024-01-09T16:30:00Z",
        }

        result = sync_repository(str(sample_repository.id), github_stats)

        # Verify result
        assert result["status"] == "success"
        assert result["action"] == "updated"
        assert result["repository_name"] == sample_repository.full_name

        # Verify git operations
        mock_git_repo_class.assert_called_once_with(repo_workdir)
        mock_origin.fetch.assert_called_once()
        mock_repo.git.reset.assert_called_once_with(
            "--hard", f"origin/{sample_repository.default_branch}"
        )

        # Verify scan task was triggered with provided GitHub stats
        mock_scan_delay.assert_called_once_with(str(sample_repository.id), github_stats)

        # Verify database updates
        db.refresh(sample_repository)
        assert sample_repository.sync_status == SyncStatus.SUCCESS
        assert sample_repository.last_sync_at is not None


@patch("kubestats.tasks.sync_repositories.settings")
@patch("kubestats.tasks.sync_repositories.git.Repo")
@patch("kubestats.tasks.scan_repositories.scan_repository.delay")
def test_sync_single_repository_no_stats(
    mock_scan_delay: Mock,
    mock_git_repo_class: Mock,
    mock_settings: Mock,
    db: Session,
    sample_repository: Repository,
) -> None:
    """Test syncing a repository with no GitHub stats provided."""
    # Setup temporary directory with existing git repo
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir
        repo_workdir = Path(temp_dir) / str(sample_repository.id)
        repo_workdir.mkdir(parents=True)
        git_dir = repo_workdir / ".git"
        git_dir.mkdir()

        # Mock git operations
        mock_repo = MagicMock()
        mock_origin = MagicMock()
        mock_repo.remotes.origin = mock_origin
        mock_git_repo_class.return_value = mock_repo

        # Mock scan task
        mock_task = Mock()
        mock_task.id = "scan-task-id"
        mock_scan_delay.return_value = mock_task

        # Add repository to session
        db.add(sample_repository)
        db.commit()

        # Test with no GitHub stats provided
        result = sync_repository(str(sample_repository.id))

        # Verify result
        assert result["status"] == "success"
        assert result["action"] == "updated"
        assert result["repository_name"] == sample_repository.full_name

        # Verify scan task was triggered with None stats
        mock_scan_delay.assert_called_once_with(str(sample_repository.id), None)


def test_sync_single_repository_not_found(db: Session) -> None:
    """Test syncing a repository that doesn't exist."""
    non_existent_id = str(uuid.uuid4())

    with pytest.raises(ValueError, match=f"Repository {non_existent_id} not found"):
        sync_repository(non_existent_id)


@patch("kubestats.tasks.sync_repositories.settings")
@patch("kubestats.tasks.sync_repositories.git.Repo")
def test_sync_single_repository_git_error(
    mock_git_repo: Mock, mock_settings: Mock, db: Session, sample_repository: Repository
) -> None:
    """Test handling of git errors during sync."""
    # Setup temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir

        # Mock git operations to raise an error
        mock_git_repo.clone_from.side_effect = Exception("Git clone failed")

        # Add repository to session
        db.add(sample_repository)
        db.commit()

        # The task should handle the exception and update the repository status
        with pytest.raises(Exception):  # noqa: B017
            sync_repository(str(sample_repository.id))

        # Verify database updates show error status
        db.refresh(sample_repository)
        assert sample_repository.sync_status == SyncStatus.ERROR
        assert sample_repository.sync_error is not None
        assert "Git clone failed" in sample_repository.sync_error


@patch("kubestats.tasks.sync_repositories.settings")
def test_cleanup_repository_workdirs_no_workdir(mock_settings: Mock) -> None:
    """Test cleanup when work directory doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir + "/nonexistent"

        result = cleanup_repository_workdirs()

        assert result["message"] == "Work directory does not exist"
        assert result["cleaned"] == 0


@patch("kubestats.tasks.sync_repositories.settings")
def test_cleanup_repository_workdirs_with_orphans(
    mock_settings: Mock, db: Session, sample_repository: Repository
) -> None:
    """Test cleanup of orphaned repository directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir
        workdir_base = Path(temp_dir)

        # Create directories for active and orphaned repositories
        active_repo_dir = workdir_base / str(sample_repository.id)
        orphaned_repo_dir = workdir_base / str(uuid.uuid4())

        active_repo_dir.mkdir()
        orphaned_repo_dir.mkdir()

        # Add only the active repository to the database
        db.add(sample_repository)
        db.commit()

        result = cleanup_repository_workdirs()

        assert result["cleaned"] == 1
        assert "Cleaned up 1 orphaned repository directories" in result["message"]

        # Verify the active repo directory still exists
        assert active_repo_dir.exists()
        # Verify the orphaned directory was removed
        assert not orphaned_repo_dir.exists()


@patch("kubestats.tasks.sync_repositories.settings")
def test_cleanup_repository_workdirs_error_handling(
    mock_settings: Mock, db: Session
) -> None:
    """Test cleanup error handling when directory removal fails."""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_settings.REPO_WORKDIR = temp_dir
        workdir_base = Path(temp_dir)

        # Create orphaned directory
        orphaned_repo_dir = workdir_base / str(uuid.uuid4())
        orphaned_repo_dir.mkdir()

        # Mock shutil.rmtree to fail
        with patch(
            "kubestats.tasks.sync_repositories.shutil.rmtree",
            side_effect=Exception("Permission denied"),
        ):
            result = cleanup_repository_workdirs()

            # Should not fail completely, but report 0 cleaned
            assert result["cleaned"] == 0
            assert "Cleaned up 0 orphaned repository directories" in result["message"]
