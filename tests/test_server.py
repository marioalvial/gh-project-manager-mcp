# tests/test_server.py
"""Tests for the MCP server entry point and initialization."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    pass


class TestServerInitialization:
    """Tests for the server initialization and functionality."""

    def test_server_initialization(self) -> None:
        """Verify main initializes FastMCP and registers tools.

        Given: The server module needs to be initialized.
        When: The server.py's main() function is executed.
        Then: - An instance using the FastMCP class is created.
              - issues.init_tools should be called once with the created instance.
              - pull_requests.init_tools should be called once with the
                created instance.
        """
        # Given
        with (
            patch("gh_project_manager_mcp.server.FastMCP") as mock_fastmcp_constructor,
            patch(
                "gh_project_manager_mcp.server.issue_tools.init_tools"
            ) as mock_issue_init,
            patch("gh_project_manager_mcp.server.pr_tools.init_tools") as mock_pr_init,
            patch(
                "gh_project_manager_mcp.server.gh_utils.get_github_token",
                return_value="mock_token",
            ) as mock_get_token,
        ):
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
                    "An MCP server wrapping the GitHub CLI (`gh`) for project "
                    "management tasks."
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

    def test_missing_github_token(self) -> None:
        """Verify the server exits if no GitHub token is found.

        Given: No GitHub token is available
        When: main() is called
        Then: The function should exit with code 1
        """
        # Given
        with (
            patch(
                "gh_project_manager_mcp.server.gh_utils.get_github_token",
                return_value=None,
            ) as mock_get_token,
            patch("sys.exit") as mock_exit,
        ):
            # When
            from gh_project_manager_mcp.server import main

            main()

            # Then
            mock_get_token.assert_called_once()
            mock_exit.assert_called_once_with(1)

    def test_main_initialization_with_token(self) -> None:
        """Test Plan.

        Given: - The get_github_token function returns a valid token.
        When:  - The main() function is called.
        Then: - An instance using the FastMCP class is created.
              - issues.init_tools should be called once with the created instance.
              - pull_requests.init_tools should be called once with
                the created instance.
        """
        # Given
        with (
            patch("gh_project_manager_mcp.server.FastMCP") as mock_fastmcp_constructor,
            patch(
                "gh_project_manager_mcp.server.issue_tools.init_tools"
            ) as mock_issue_init,
            patch("gh_project_manager_mcp.server.pr_tools.init_tools") as mock_pr_init,
            patch(
                "gh_project_manager_mcp.server.gh_utils.get_github_token",
                return_value="mock_token",
            ) as mock_get_token,
        ):
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
                    "An MCP server wrapping the GitHub CLI (`gh`) for "
                    "project management tasks."
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

    def test_main_initialization_without_token(self) -> None:
        """Test Plan.

        Given: - The get_github_token function returns None.
        When:  - The main() function is called.
        Then: - A warning about the missing token is printed.
              - An instance using the FastMCP class is created.
              - issues.init_tools should be called once.
              - pull_requests.init_tools should be called once.
        """
        # Given
        with (
            patch(
                "gh_project_manager_mcp.server.gh_utils.get_github_token",
                return_value=None,
            ) as mock_get_token,
            patch("sys.exit") as mock_exit,
        ):
            # When
            from gh_project_manager_mcp.server import main

            main()

            # Then
            mock_get_token.assert_called_once()
            mock_exit.assert_called_once_with(1)

    def test_fastmcp_instance_creation(self) -> None:
        """Verify FastMCP is instantiated with correct parameters."""
        with (
            patch("gh_project_manager_mcp.server.FastMCP") as mock_fast_mcp,
            patch(
                "gh_project_manager_mcp.server.gh_utils.get_github_token",
                return_value="mock_token",
            ),
        ):
            # When
            from gh_project_manager_mcp.server import main

            main()

            # Then
            mock_fast_mcp.assert_called_once_with(
                title="GitHub Project Manager MCP",
                description=(
                    "An MCP server wrapping the GitHub CLI (`gh`) for "
                    "project management tasks."
                ),
                version="0.1.0",
            )


# Add other tests for server functionality as needed
