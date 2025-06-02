"""
Tests for repository metrics saving tasks.
"""

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import desc
from sqlmodel import Session, select

from kubestats.models import Repository, RepositoryMetrics
from kubestats.tasks.save_repository_metrics import (
    parse_github_stats,
    save_repository_metrics,
)


@pytest.fixture
def mock_github_data() -> dict[str, Any]:
    """Mock GitHub API response data."""
    return {
        "id": 12345,
        "name": "test-repo",
        "full_name": "testowner/test-repo",
        "stargazers_count": 100,
        "forks_count": 25,
        "watchers_count": 75,
        "open_issues_count": 5,
        "size": 1024,
        "updated_at": "2024-01-15T10:30:00Z",
        "pushed_at": "2024-01-14T15:45:00Z",
    }


@pytest.fixture
def test_repository(db: Any) -> Repository:
    """Create a test repository."""
    # Generate unique IDs to avoid conflicts
    unique_id = uuid.uuid4()
    github_id = hash(str(unique_id)) % 100000000  # Generate a unique positive integer

    repository = Repository(
        github_id=abs(github_id),  # Ensure positive
        name=f"test-repo-{unique_id.hex[:8]}",
        full_name=f"testowner/test-repo-{unique_id.hex[:8]}",
        owner="testowner",
        description="A test repository",
        language="Python",
        topics=["test", "kubernetes"],
        default_branch="main",
        created_at=datetime.now(timezone.utc),
    )
    db.add(repository)
    db.commit()
    db.refresh(repository)
    return repository


def test_parse_github_stats(mock_github_data: dict[str, Any]) -> None:
    """Test parsing GitHub repository data to metrics format."""
    metrics = parse_github_stats(mock_github_data)

    assert metrics["stars_count"] == 100
    assert metrics["forks_count"] == 25
    assert metrics["watchers_count"] == 75
    assert metrics["open_issues_count"] == 5
    assert metrics["size"] == 1024
    assert isinstance(metrics["updated_at"], datetime)
    assert isinstance(metrics["pushed_at"], datetime)


def test_parse_github_stats_no_pushed_at() -> None:
    """Test parsing GitHub data when pushed_at is None."""
    data = {
        "stargazers_count": 10,
        "forks_count": 2,
        "watchers_count": 8,
        "open_issues_count": 1,
        "size": 512,
        "updated_at": "2024-01-15T10:30:00Z",
        "pushed_at": None,
    }

    metrics = parse_github_stats(data)
    assert metrics["pushed_at"] is None
    assert metrics["stars_count"] == 10


@patch("kubestats.tasks.save_repository_metrics.get_repository")
def test_save_repository_metrics_success(
    mock_get_repo: Mock,
    test_repository: Repository,
    db: Session,
    mock_github_data: dict[str, Any],
) -> None:
    """Test successful repository metrics saving."""
    mock_get_repo.return_value = mock_github_data

    # Execute the task
    result = save_repository_metrics(
        str(test_repository.id), kubernetes_resources_count=5
    )

    # Verify the result
    assert result["status"] == "success"
    assert result["repository_id"] == str(test_repository.id)
    assert result["repository_name"] == test_repository.full_name
    assert result["metrics"]["kubernetes_resources_count"] == 5
    assert result["metrics"]["stars_count"] == 100

    # Verify metrics were saved to database
    metrics = db.exec(
        select(RepositoryMetrics).where(
            RepositoryMetrics.repository_id == test_repository.id
        )
    ).first()

    assert metrics is not None
    assert metrics.stars_count == 100
    assert metrics.forks_count == 25
    assert metrics.kubernetes_resources_count == 5


@patch("kubestats.tasks.save_repository_metrics.get_repository")
def test_save_repository_metrics_github_api_failure_with_previous_metrics(
    mock_get_repo: Mock, test_repository: Repository, db: Session
) -> None:
    """Test metrics saving when GitHub API fails but previous metrics exist."""
    # Create previous metrics
    previous_metrics = RepositoryMetrics(
        repository_id=test_repository.id,
        stars_count=50,
        forks_count=10,
        watchers_count=40,
        open_issues_count=2,
        size=512,
        kubernetes_resources_count=3,
        updated_at=datetime.now(timezone.utc),
        pushed_at=None,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(previous_metrics)
    db.commit()

    # Mock GitHub API failure
    mock_get_repo.side_effect = Exception("GitHub API error")

    # Execute the task
    result = save_repository_metrics(
        str(test_repository.id), kubernetes_resources_count=7
    )

    # Verify it used previous metrics
    assert result["status"] == "success"
    assert result["metrics"]["stars_count"] == 50  # From previous metrics
    assert result["metrics"]["kubernetes_resources_count"] == 7  # New value

    # Verify new metrics were saved
    new_metrics = db.exec(
        select(RepositoryMetrics)
        .where(RepositoryMetrics.repository_id == test_repository.id)
        .order_by(desc(RepositoryMetrics.recorded_at))  # type: ignore[arg-type]
    ).first()

    assert new_metrics is not None
    assert new_metrics.stars_count == 50
    assert new_metrics.kubernetes_resources_count == 7


@patch("kubestats.tasks.save_repository_metrics.get_repository")
def test_save_repository_metrics_github_api_failure_no_previous_metrics(
    mock_get_repo: Mock, test_repository: Repository, db: Session
) -> None:
    """Test metrics saving when GitHub API fails and no previous metrics exist."""
    # Mock GitHub API failure
    mock_get_repo.side_effect = Exception("GitHub API error")

    # Execute the task
    result = save_repository_metrics(
        str(test_repository.id), kubernetes_resources_count=3
    )

    # Verify it used default values
    assert result["status"] == "success"
    assert result["metrics"]["stars_count"] == 0  # Default value
    assert result["metrics"]["kubernetes_resources_count"] == 3  # New value

    # Verify metrics were saved
    metrics = db.exec(
        select(RepositoryMetrics).where(
            RepositoryMetrics.repository_id == test_repository.id
        )
    ).first()

    assert metrics is not None
    assert metrics.stars_count == 0
    assert metrics.kubernetes_resources_count == 3


def test_save_repository_metrics_repository_not_found(db: Session) -> None:
    """Test error handling when repository doesn't exist."""
    non_existent_id = str(uuid.uuid4())

    with pytest.raises(ValueError, match="Repository .* not found"):
        save_repository_metrics(non_existent_id, kubernetes_resources_count=1)


def test_save_repository_metrics_with_provided_github_stats(
    test_repository: Repository, db: Session
) -> None:
    """Test metrics saving when GitHub stats are provided directly."""
    # Provide GitHub stats directly (no API call needed)
    github_stats = {
        "stars_count": 150,
        "forks_count": 30,
        "watchers_count": 120,
        "open_issues_count": 8,
        "size": 2048,
        "updated_at": "2024-01-20T12:00:00Z",
        "pushed_at": "2024-01-19T16:30:00Z",
    }

    # Execute the task with provided stats
    result = save_repository_metrics(
        str(test_repository.id), kubernetes_resources_count=5, github_stats=github_stats
    )

    # Verify the result uses provided stats
    assert result["status"] == "success"
    assert result["metrics"]["stars_count"] == 150
    assert result["metrics"]["forks_count"] == 30
    assert result["metrics"]["kubernetes_resources_count"] == 5

    # Verify metrics were saved to database
    metrics = db.exec(
        select(RepositoryMetrics).where(
            RepositoryMetrics.repository_id == test_repository.id
        )
    ).first()

    assert metrics is not None
    assert metrics.stars_count == 150
    assert metrics.forks_count == 30
    assert metrics.kubernetes_resources_count == 5


@patch("kubestats.tasks.save_repository_metrics.get_repository")
def test_save_repository_metrics_zero_kubernetes_resources(
    mock_get_repo: Mock,
    test_repository: Repository,
    db: Session,
    mock_github_data: dict[str, Any],
) -> None:
    """Test metrics saving with zero Kubernetes resources."""
    mock_get_repo.return_value = mock_github_data

    # Execute the task with zero resources
    result = save_repository_metrics(
        str(test_repository.id), kubernetes_resources_count=0
    )

    # Verify the result
    assert result["status"] == "success"
    assert result["metrics"]["kubernetes_resources_count"] == 0

    # Verify metrics were saved correctly
    metrics = db.exec(
        select(RepositoryMetrics).where(
            RepositoryMetrics.repository_id == test_repository.id
        )
    ).first()

    assert metrics is not None
    assert metrics.kubernetes_resources_count == 0
    assert metrics.stars_count == 100  # GitHub data should still be saved


@patch("kubestats.tasks.save_repository_metrics.get_repository")
def test_save_repository_metrics_with_incomplete_github_stats(
    mock_get_repo: Mock,
    test_repository: Repository,
    db: Session,
    mock_github_data: dict[str, Any],
) -> None:
    """Test that missing fields in provided GitHub stats are fetched from API."""
    mock_get_repo.return_value = mock_github_data

    # Provide incomplete GitHub stats (missing some required fields)
    incomplete_stats = {
        "stars_count": 50,  # Provided
        "forks_count": 10,  # Provided
        # Missing: watchers_count, open_issues_count, size, updated_at
        "pushed_at": "2024-01-14T14:20:00Z",
    }

    # Execute the task with incomplete stats
    result = save_repository_metrics(
        str(test_repository.id),
        kubernetes_resources_count=3,
        github_stats=incomplete_stats,
    )

    # Verify the result
    assert result["status"] == "success"
    assert result["repository_id"] == str(test_repository.id)
    assert result["metrics"]["kubernetes_resources_count"] == 3
    # Should use provided values
    assert result["metrics"]["stars_count"] == 50
    assert result["metrics"]["forks_count"] == 10
    # Should fetch missing values from API
    assert result["metrics"]["watchers_count"] == 75  # From mock_github_data
    assert result["metrics"]["open_issues_count"] == 5  # From mock_github_data
    assert result["metrics"]["size"] == 1024  # From mock_github_data

    # Verify API was called to fetch missing data
    mock_get_repo.assert_called_once_with(test_repository.owner, test_repository.name)

    # Verify metrics were saved to database with merged data
    metrics = db.exec(
        select(RepositoryMetrics).where(
            RepositoryMetrics.repository_id == test_repository.id
        )
    ).first()

    assert metrics is not None
    assert metrics.stars_count == 50  # From provided stats
    assert metrics.forks_count == 10  # From provided stats
    assert metrics.watchers_count == 75  # From API
    assert metrics.open_issues_count == 5  # From API
    assert metrics.size == 1024  # From API
    assert metrics.kubernetes_resources_count == 3


@patch("kubestats.tasks.save_repository_metrics.get_repository")
def test_save_repository_metrics_incomplete_stats_api_failure(
    mock_get_repo: Mock, test_repository: Repository, db: Session
) -> None:
    """Test handling when provided stats are incomplete and API call fails."""
    # Mock API failure
    mock_get_repo.side_effect = Exception("GitHub API error")

    # Provide incomplete GitHub stats
    incomplete_stats = {
        "stars_count": 30,
        # Missing other required fields
    }

    # Execute the task
    result = save_repository_metrics(
        str(test_repository.id),
        kubernetes_resources_count=2,
        github_stats=incomplete_stats,
    )

    # Verify the result - should still succeed with defaults for missing fields
    assert result["status"] == "success"
    assert result["metrics"]["stars_count"] == 30  # From provided stats
    assert result["metrics"]["forks_count"] == 0  # Default for missing field
    assert result["metrics"]["watchers_count"] == 0  # Default for missing field
    assert result["metrics"]["kubernetes_resources_count"] == 2


def test_parse_github_stats_with_different_field_names() -> None:
    """Test parsing GitHub stats with both API format (stargazers_count) and our format (stars_count)."""
    # Test with API format
    api_data = {
        "stargazers_count": 100,  # GitHub API uses this field name
        "forks_count": 25,
        "watchers_count": 75,
        "open_issues_count": 5,
        "size": 1024,
        "updated_at": "2024-01-15T10:30:00Z",
        "pushed_at": "2024-01-14T14:20:00Z",
    }

    metrics = parse_github_stats(api_data)
    assert metrics["stars_count"] == 100

    # Test with our internal format
    internal_data = {
        "stars_count": 200,  # Our internal format uses this field name
        "forks_count": 50,
        "watchers_count": 150,
        "open_issues_count": 10,
        "size": 2048,
        "updated_at": "2024-01-15T10:30:00Z",
        "pushed_at": "2024-01-14T14:20:00Z",
    }

    metrics = parse_github_stats(internal_data)
    assert metrics["stars_count"] == 200
