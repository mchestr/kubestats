"""
Unit tests for GitHub API client.
Tests the search_repositories function with various scenarios including
successful requests, authentication, error handling, and edge cases.
"""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from kubestats.core.github_client import search_repositories


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_success_with_auth(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test successful repository search with GitHub token authentication."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 2,
        "incomplete_results": False,
        "items": [
            {
                "id": 123456,
                "name": "kubernetes",
                "full_name": "kubernetes/kubernetes",
                "html_url": "https://github.com/kubernetes/kubernetes",
                "description": "Production-Grade Container Scheduling and Management",
                "stargazers_count": 95000,
                "language": "Go",
                "updated_at": "2024-01-15T10:30:00Z",
            },
            {
                "id": 789012,
                "name": "helm",
                "full_name": "helm/helm",
                "html_url": "https://github.com/helm/helm",
                "description": "The Kubernetes Package Manager",
                "stargazers_count": 25000,
                "language": "Go",
                "updated_at": "2024-01-14T15:20:00Z",
            },
        ],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function
    result = search_repositories("kubernetes")

    # Verify the result
    assert result["total_count"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "kubernetes"
    assert result["items"][1]["name"] == "helm"

    # Verify HTTP client was called correctly
    mock_client_class.assert_called_once_with(timeout=30.0)
    mock_client_instance.get.assert_called_once_with(
        "https://api.github.com/search/repositories",
        params={
            "q": "kubernetes",
            "per_page": 100,
            "sort": "updated",
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "kubestats/1.0",
            "Authorization": "Bearer ghp_test_token_123",
        },
    )
    mock_response.raise_for_status.assert_called_once()


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_success_without_auth(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test successful repository search without GitHub token (unauthenticated)."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = None
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "id": 123456,
                "name": "test-repo",
                "full_name": "user/test-repo",
                "html_url": "https://github.com/user/test-repo",
                "description": "A test repository",
                "stargazers_count": 10,
                "language": "Python",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        ],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function
    result = search_repositories("test")

    # Verify the result
    assert result["total_count"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "test-repo"

    # Verify HTTP client was called correctly (without Authorization header)
    mock_client_instance.get.assert_called_once_with(
        "https://api.github.com/search/repositories",
        params={
            "q": "test",
            "per_page": 100,
            "sort": "updated",
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "kubestats/1.0",
        },
    )


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_empty_results(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with no results found."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response with empty results
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 0,
        "incomplete_results": False,
        "items": [],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function
    result = search_repositories("nonexistent-repository-xyz-123")

    # Verify the result
    assert result["total_count"] == 0
    assert len(result["items"]) == 0

    # Verify HTTP client was called correctly
    mock_client_instance.get.assert_called_once()


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_http_error_404(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with HTTP 404 error."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response that raises 404
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found",
        request=Mock(),
        response=Mock(status_code=404),
    )

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function and expect exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        search_repositories("test")

    assert "404" in str(exc_info.value)
    mock_response.raise_for_status.assert_called_once()


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_http_error_403_rate_limit(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with HTTP 403 rate limit error."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = None  # Unauthenticated to simulate rate limiting
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response that raises 403
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403 Forbidden",
        request=Mock(),
        response=Mock(status_code=403),
    )

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function and expect exception
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        search_repositories("test")

    assert "403" in str(exc_info.value)


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_timeout_error(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with timeout error."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock client that raises timeout
    mock_client_instance = Mock()
    mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function and expect exception
    with pytest.raises(httpx.TimeoutException):
        search_repositories("test")

    # Verify timeout was configured correctly
    mock_client_class.assert_called_once_with(timeout=30.0)


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_network_error(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with network connection error."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock client that raises network error
    mock_client_instance = Mock()
    mock_client_instance.get.side_effect = httpx.ConnectError("Connection failed")
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function and expect exception
    with pytest.raises(httpx.ConnectError):
        search_repositories("test")


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_invalid_json_response(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with invalid JSON response."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response with invalid JSON
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function and expect exception
    with pytest.raises(json.JSONDecodeError):
        search_repositories("test")


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_complex_query(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with complex query parameters."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 5,
        "incomplete_results": False,
        "items": [],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function with complex query
    complex_query = "kubernetes language:go stars:>1000 created:>2020-01-01"
    result = search_repositories(complex_query)

    # Verify the result
    assert result["total_count"] == 5

    # Verify the complex query was passed correctly
    mock_client_instance.get.assert_called_once_with(
        "https://api.github.com/search/repositories",
        params={
            "q": complex_query,
            "per_page": 100,
            "sort": "updated",
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "kubestats/1.0",
            "Authorization": "Bearer ghp_test_token_123",
        },
    )


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_special_characters_in_query(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with special characters in query."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 1,
        "incomplete_results": False,
        "items": [],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function with special characters
    special_query = "test-repo_v2.0 @organization/namespace"
    result = search_repositories(special_query)

    # Verify the result
    assert result["total_count"] == 1

    # Verify the special characters were handled correctly
    mock_client_instance.get.assert_called_once()
    call_args = mock_client_instance.get.call_args
    assert call_args[1]["params"]["q"] == special_query


@patch("kubestats.core.github_client.settings")
@patch("kubestats.core.github_client.logger")
@patch("httpx.Client")
def test_search_repositories_logging(
    mock_client_class: Mock, mock_logger: Mock, mock_settings: Mock
) -> None:
    """Test that repository search logs appropriate messages."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 42,
        "incomplete_results": False,
        "items": [{"id": 1}, {"id": 2}],  # 2 items
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function
    search_repositories("test-query")

    # Verify logging calls
    mock_logger.info.assert_any_call("Searching GitHub with query: test-query")
    mock_logger.debug.assert_called_with("Using authenticated GitHub API request")
    mock_logger.info.assert_any_call(
        "GitHub search completed: 42 total repositories found, returning 2 repositories"
    )


@patch("kubestats.core.github_client.settings")
@patch("kubestats.core.github_client.logger")
@patch("httpx.Client")
def test_search_repositories_logging_unauthenticated(
    mock_client_class: Mock, mock_logger: Mock, mock_settings: Mock
) -> None:
    """Test logging for unauthenticated requests."""
    # Setup mock settings
    mock_settings.GITHUB_TOKEN = None
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 0,
        "incomplete_results": False,
        "items": [],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function
    search_repositories("test")

    # Verify unauthenticated logging
    mock_logger.debug.assert_called_with(
        "Using unauthenticated GitHub API request (60 requests/hour limit)"
    )


@patch("kubestats.core.github_client.settings")
@patch("httpx.Client")
def test_search_repositories_custom_api_base_url(
    mock_client_class: Mock, mock_settings: Mock
) -> None:
    """Test repository search with custom GitHub API base URL."""
    # Setup mock settings with custom base URL
    mock_settings.GITHUB_TOKEN = "ghp_test_token_123"
    mock_settings.GITHUB_API_BASE_URL = "https://api.github.enterprise.com"

    # Setup mock HTTP response
    mock_response = Mock()
    mock_response.json.return_value = {
        "total_count": 1,
        "incomplete_results": False,
        "items": [],
    }
    mock_response.raise_for_status.return_value = None

    # Setup mock client
    mock_client_instance = Mock()
    mock_client_instance.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client_instance

    # Execute the function
    search_repositories("test")

    # Verify custom base URL was used
    mock_client_instance.get.assert_called_once_with(
        "https://api.github.enterprise.com/search/repositories",
        params={
            "q": "test",
            "per_page": 100,
            "sort": "updated",
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "kubestats/1.0",
            "Authorization": "Bearer ghp_test_token_123",
        },
    )
