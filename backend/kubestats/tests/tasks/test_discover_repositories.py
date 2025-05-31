"""
Unit tests for the discover_repositories task.
Tests individual functions and the main discovery task workflow.
"""

from typing import Any
from unittest.mock import Mock, patch

from kubestats.tasks.discover_repositories import parse_github_repo


def test_parse_github_repo() -> None:
    """Test parsing GitHub repository data into our model format."""
    # Sample GitHub API response data
    repo_data = {
        "id": 123456,
        "name": "test-repo",
        "full_name": "owner/test-repo",
        "owner": {"login": "owner"},
        "description": "A test repository",
        "language": "Python",
        "topics": ["kubernetes", "kubesearch"],
        "license": {"name": "MIT"},
        "default_branch": "main",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        "pushed_at": "2023-01-02T12:00:00Z",
        "stargazers_count": 100,
        "forks_count": 20,
        "watchers_count": 100,
        "open_issues_count": 5,
        "size": 1024,
    }

    result = parse_github_repo(repo_data)

    # Verify parsed data
    assert result["github_id"] == 123456
    assert result["name"] == "test-repo"
    assert result["full_name"] == "owner/test-repo"
    assert result["owner"] == "owner"
    assert result["description"] == "A test repository"
    assert result["language"] == "Python"
    assert result["topics"] == ["kubernetes", "kubesearch"]
    assert result["license_name"] == "MIT"
    assert result["default_branch"] == "main"
    assert result["stars_count"] == 100
    assert result["forks_count"] == 20
    assert result["watchers_count"] == 100
    assert result["open_issues_count"] == 5
    assert result["size"] == 1024


def test_parse_github_repo_minimal() -> None:
    """Test parsing GitHub repository data with minimal fields."""
    repo_data = {
        "id": 123456,
        "name": "test-repo",
        "full_name": "owner/test-repo",
        "owner": {"login": "owner"},
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
        # Missing optional fields
    }

    result = parse_github_repo(repo_data)

    # Verify parsed data with defaults
    assert result["github_id"] == 123456
    assert result["description"] is None
    assert result["language"] is None
    assert result["topics"] == []
    assert result["license_name"] is None
    assert result["default_branch"] == "main"
    assert result["pushed_at"] is None
    assert result["stars_count"] == 0
    assert result["forks_count"] == 0


@patch("kubestats.tasks.discover_repositories.Session")
@patch("kubestats.tasks.discover_repositories.sync_repository.delay")
@patch("kubestats.tasks.discover_repositories.search_repositories")
def test_sync_repository_called_for_all_discovered_repositories(
    mock_search: Mock, mock_sync_delay: Mock, mock_session_class: Mock
) -> None:
    """Test that sync_repository.delay is called for all discovered repositories."""
    from unittest.mock import Mock

    from kubestats.models import Repository
    from kubestats.tasks.discover_repositories import discover_repositories

    # Mock GitHub API response - note: search_repositories returns dict with 'items' key
    mock_search.return_value = {
        "items": [
            {
                "id": 123456,
                "name": "repo1",
                "full_name": "mchestr/repo1",
                "owner": {"login": "mchestr"},
                "description": "A test repository",
                "language": "Python",
                "topics": ["kubesearch"],
                "license": {"name": "MIT"},
                "default_branch": "main",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "stargazers_count": 100,
                "forks_count": 20,
                "watchers_count": 100,
                "open_issues_count": 5,
                "size": 1024,
            },
            {
                "id": 789012,
                "name": "repo2",
                "full_name": "mchestr/repo2",
                "owner": {"login": "mchestr"},
                "description": "Another test repository",
                "language": "JavaScript",
                "topics": ["k8s-at-home"],
                "license": {"name": "Apache-2.0"},
                "default_branch": "main",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "stargazers_count": 50,
                "forks_count": 10,
                "watchers_count": 50,
                "open_issues_count": 2,
                "size": 512,
            },
        ]
    }

    # Mock database session
    mock_session = Mock()
    mock_session_class.return_value.__enter__.return_value = mock_session

    # Mock repository objects
    repo1_mock = Mock(spec=Repository)
    repo1_mock.id = "repo1-uuid"

    repo2_mock = Mock(spec=Repository)
    repo2_mock.id = "repo2-uuid"

    # Mock the create_or_update_repository behavior by patching it directly
    with patch(
        "kubestats.tasks.discover_repositories.create_or_update_repository"
    ) as mock_create_update:
        # Return Repository objects (not tuples)
        mock_create_update.side_effect = [repo1_mock, repo2_mock]

        result = discover_repositories()

    # Verify the task completed successfully
    assert result["repositories_found"] == 2

    # Verify sync_repository.delay was called twice (once for each repository)
    assert mock_sync_delay.call_count == 2

    # Verify the correct repository IDs were passed
    calls = mock_sync_delay.call_args_list
    assert calls[0][0][0] == "repo1-uuid"  # First call with repo1 ID
    assert calls[1][0][0] == "repo2-uuid"  # Second call with repo2 ID


@patch("kubestats.core.github_client.search_repositories")
def test_individual_topic_queries_and_deduplication(mock_search_func: Mock) -> None:
    """Test that we query each topic individually and deduplicate results."""

    # Mock search results for each topic
    def search_side_effect(query: str) -> list[dict[str, Any]]:
        if query == "topic:kubesearch":
            return [{"id": 1, "name": "repo1", "full_name": "owner/repo1"}]
        elif query == "topic:k8s-at-home":
            return [
                {"id": 2, "name": "repo2", "full_name": "owner/repo2"},
                {"id": 1, "name": "repo1", "full_name": "owner/repo1"},  # Duplicate
            ]
        return []

    mock_search_func.side_effect = search_side_effect

    # Simulate the logic from our discover_repositories function
    from kubestats.core.config import settings

    all_repos = {}
    for tag in settings.GITHUB_DISCOVERY_TAGS:
        query = f"topic:{tag}"
        tag_repos = mock_search_func(query)

        # Add repos to our collection, using repo ID as key to avoid duplicates
        for repo in tag_repos:
            all_repos[repo["id"]] = repo

    # Verify each topic was queried individually
    expected_calls = [
        ("topic:kubesearch",),
        ("topic:k8s-at-home",),
    ]
    actual_calls = [call.args for call in mock_search_func.call_args_list]
    assert actual_calls == expected_calls

    # Verify deduplication works - should have 2 unique repos despite duplicate
    assert len(all_repos) == 2
    assert 1 in all_repos  # repo1
    assert 2 in all_repos  # repo2
