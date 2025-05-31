"""
GitHub API client for repository operations.
This module provides a simple interface to access GitHub's public API.
"""

import logging
from typing import Any

import httpx

from kubestats.core.config import settings

logger = logging.getLogger(__name__)


def get_repository(owner: str, repo: str) -> dict[str, Any]:
    """
    Fetch detailed information for a single repository from GitHub API.

    Args:
        owner: Repository owner (username or organization)
        repo: Repository name

    Returns:
        Dictionary containing repository data from GitHub API

    Raises:
        httpx.HTTPStatusError: If the API request fails
    """
    logger.info(f"Fetching repository data for {owner}/{repo}")

    # Prepare headers
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "kubestats/1.0",
    }

    # Add authentication if token is provided
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        logger.debug("Using authenticated GitHub API request")
    else:
        logger.debug(
            "Using unauthenticated GitHub API request (60 requests/hour limit)"
        )

    # Make the API request using synchronous client
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}",
            headers=headers,
        )

        # Raise an exception for HTTP errors
        response.raise_for_status()

        # Parse JSON response
        result: dict[str, Any] = response.json()

        logger.info(f"Successfully fetched repository data for {owner}/{repo}")

        return result


def search_repositories(query: str) -> dict[str, Any]:
    """
    Synchronous implementation of GitHub repository search.
    """
    logger.info(f"Searching GitHub with query: {query}")

    # Prepare headers
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "kubestats/1.0",
    }

    # Add authentication if token is provided
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        logger.debug("Using authenticated GitHub API request")
    else:
        logger.debug(
            "Using unauthenticated GitHub API request (60 requests/hour limit)"
        )

    # Make the API request using synchronous client
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            f"{settings.GITHUB_API_BASE_URL}/search/repositories",
            params={
                "q": query,
                "per_page": 100,  # Maximum allowed by GitHub
                "sort": "updated",  # Get most recently updated repos first
            },
            headers=headers,
        )

        # Raise an exception for HTTP errors
        response.raise_for_status()

        # Parse JSON response
        result: dict[str, Any] = response.json()

        logger.info(
            f"GitHub search completed: {result.get('total_count', 0)} total repositories found, "
            f"returning {len(result.get('items', []))} repositories"
        )

        return result
