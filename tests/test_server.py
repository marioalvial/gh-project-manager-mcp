# tests/test_server.py
"""Tests for the MCP server entry point and initialization."""

import sys
from typing import Any, Dict, TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestServerInitialization:
    """Tests for the server initialization and functionality."""

    def test_server_initialization(self) -> None:
        """Verify main initializes FastMCP and registers tools.

        Given: The server module needs to be initialized.
        When: The server.py's main() function is executed.
        Then: - An instance using the FastMCP class is created.
              - issues.init_tools should be called once with the created instance.
              - pull_requests.init_tools should be called once with the created instance.
        """
        # Given
        with patch("gh_project_manager_mcp.server.FastMCP") as mock_fastmcp_constructor, \
             patch("gh_project_manager_mcp.server.issue_tools.init_tools") as mock_issue_init, \
             patch("gh_project_manager_mcp.server.pr_tools.init_tools") as mock_pr_init, \
             patch("gh_project_manager_mcp.server.gh_utils.get_github_token", return_value="mock_token") as mock_get_token:

            # Configure the mock constructor
            mock_server_instance = MagicMock()
            mock_fastmcp_constructor.return_value = mock_server_instance

            # When
            # Import after patching to ensure our mocks are in place
            from gh_project_manager_mcp.server import main
            result = main()

            # Then
            # 1. Verify FastMCP constructor was called correctly
            mock_fastmcp_constructor.assert_called_once_with(
                title="GitHub Project Manager MCP",
                description=(
                    "An MCP server wrapping the GitHub CLI (`gh`) for project management "
                    "tasks."
                ),
                version="0.1.0",
            )
            
            # 2. Verify token was checked
            mock_get_token.assert_called_once()
            
            # 3. init_tools called with the mock instance
            mock_issue_init.assert_called_once_with(mock_server_instance)
            mock_pr_init.assert_called_once_with(mock_server_instance)
            
            # 4. Check the result is the server instance
            assert result == mock_server_instance

    def test_server_start(self) -> None:
        """Verify the start_server function starts uvicorn correctly.
        
        Given: A FastMCP server instance
        When: start_server is called with that instance
        Then: uvicorn.run is called with the correct parameters
        """
        # Given
        with patch("gh_project_manager_mcp.server.uvicorn.run") as mock_uvicorn_run:
            mock_server = MagicMock()
            
            # When
            from gh_project_manager_mcp.server import start_server
            start_server(mock_server)
            
            # Then
            mock_uvicorn_run.assert_called_once_with(
                mock_server,
                host="0.0.0.0",
                port=8191
            )

    def test_missing_github_token(self) -> None:
        """Verify the server exits if no GitHub token is found.
        
        Given: No GitHub token is available
        When: main() is called
        Then: The function should exit with code 1
        """
        # Given
        with patch("gh_project_manager_mcp.server.gh_utils.get_github_token", return_value=None) as mock_get_token, \
             patch("sys.exit") as mock_exit:
            
            # When
            from gh_project_manager_mcp.server import main
            main()
            
            # Then
            mock_get_token.assert_called_once()
            mock_exit.assert_called_once_with(1)

# Add other tests for server functionality as needed
