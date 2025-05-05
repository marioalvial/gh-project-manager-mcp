"""Common fixtures for GitHub Project Manager MCP integration tests."""

import os
import random
import re
import string
import time
from typing import Any, Callable, Dict, List

import pytest
from gh_project_manager_mcp.utils.error import Error
from result import Ok, Result


@pytest.fixture(scope="module")
def gh_token() -> str:
    """Get GitHub token from environment variable.

    Returns
    -------
        GitHub token from GH_TOKEN environment variable

    """
    token = os.environ.get("GH_TOKEN")
    if not token:
        # Try to load from .env file if exists
        try:
            from dotenv import load_dotenv

            load_dotenv()
            token = os.environ.get("GH_TOKEN")
        except ImportError:
            pass

    assert token, "GH_TOKEN environment variable is required for tests"
    return token


@pytest.fixture(scope="module")
def test_repo_info() -> Dict[str, str]:
    """Get test repository information from environment variables.

    Returns
    -------
        Dictionary with owner and repo keys

    """
    # Try to load from .env file if exists
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    owner = os.environ.get("GH_REPO_OWNER")
    repo = os.environ.get("GH_REPO_NAME")

    assert owner, "GH_REPO_OWNER environment variable is required for tests"
    assert repo, "GH_REPO_NAME environment variable is required for tests"

    return {"owner": owner, "repo": repo}


@pytest.fixture(scope="module")
def random_string_generator() -> Callable[[str], str]:
    """Create a function to generate random strings with prefix.

    Returns
    -------
        Function that takes a prefix and returns a random string

    """

    def generate(prefix: str) -> str:
        """Generate a random string with the given prefix.

        Args:
        ----
            prefix: Prefix for the random string

        Returns:
        -------
            String with format: prefix-timestamp-randomchars

        """
        timestamp = int(time.time())
        random_part = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        return f"{prefix}-{timestamp}-{random_part}"

    return generate


@pytest.fixture(scope="module")
def clean_up_resources() -> Dict[str, List[Dict[str, Any]]]:
    """Create a dict to store resources created during tests.

    Returns
    -------
        Dictionary with lists for different resource types

    """
    return {
        "issues": [],
        "pull_requests": [],
        "projects": [],
    }


def extract_github_number_from_url(url: str, resource_type: str = "issues") -> int:
    """Extract resource number from a GitHub URL.

    Args:
    ----
        url: GitHub URL (e.g., https://github.com/owner/repo/issues/123)
        resource_type: Type of resource (issues, pull, projects, etc.)

    Returns:
    -------
        Resource number as integer

    Raises:
    ------
        ValueError: If URL doesn't contain a resource number

    """
    pattern = rf"/{resource_type}/(\d+)"
    match = re.search(pattern, url)
    if match:
        return int(match.group(1))
    raise ValueError(f"Could not extract {resource_type} number from URL: {url}")


def process_github_result(
    result: Result[str, Error], resource_type: str = "issues"
) -> Dict[str, Any]:
    """Process result from GitHub API to ensure it contains all required fields.

    Args:
    ----
        result: Result object from API call
        resource_type: Type of resource (issues, pull, projects, etc.)

    Returns:
    -------
        Dictionary with at least number, title, and URL keys

    Raises:
    ------
        AssertionError: If result is not Ok or doesn't contain parseable data

    """
    assert isinstance(result, Ok), f"Expected Ok result but got: {result}"
    data = result.unwrap()

    # If data is a URL string, extract info and create basic object
    if isinstance(data, str) and data.startswith("http"):
        try:
            number = extract_github_number_from_url(data, resource_type)
            return {
                "number": number,
                "url": data,
                "title": f"{resource_type.capitalize()[:-1]} #{number}",  # Issue #123 or Pull #123
            }
        except ValueError as e:
            raise AssertionError(f"Failed to process {resource_type} result: {e}")

    # If data is already a dict, ensure it has number field
    if isinstance(data, dict):
        if "number" in data:
            return data
        elif "url" in data and f"/{resource_type}/" in data["url"]:
            # Try to extract number from URL if present
            try:
                data["number"] = extract_github_number_from_url(
                    data["url"], resource_type
                )
                return data
            except ValueError:
                pass

    # If we get here, data format is unexpected
    raise AssertionError(f"Unexpected response format: {data}")
