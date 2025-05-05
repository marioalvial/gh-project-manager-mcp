#!/usr/bin/env python3
"""Integration tests for GitHub CLI functionality in the MCP server."""

import json
import os
import time
import uuid
from typing import List, Tuple

import pytest

# Test configuration - will use environment variables in real tests
OWNER = os.environ.get("GITHUB_TEST_OWNER", "marioalvial")
REPO = os.environ.get("GITHUB_TEST_REPO", "gh-project-manager-mcp")
GH_TOKEN = os.environ.get("GH_TOKEN", "")  # Should be provided via environment
DOCKER_IMAGE = os.environ.get("DOCKER_IMAGE", "gh-project-manager-mcp:stdio")

# Skip all tests if no GitHub token is available
pytestmark = pytest.mark.skipif(
    not GH_TOKEN, reason="GH_TOKEN environment variable not set"
)


def generate_test_data(prefix: str = "") -> str:
    """Generate unique test data with timestamp and random suffix."""
    timestamp = int(time.time())
    random_id = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}-{timestamp}-{random_id}"
    return f"Test-{timestamp}-{random_id}"


def run_gh_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a GitHub CLI command in the Docker container and return results.

    Args:
    ----
        command: List of command parts to pass to the gh CLI

    Returns:
    -------
        Tuple of (return_code, stdout, stderr)

    """
    import subprocess

    cmd = [
        "docker",
        "run",
        "--rm",
        "-e",
        f"GH_TOKEN={GH_TOKEN}",
        DOCKER_IMAGE,
        "gh",
    ] + command

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    return result.returncode, result.stdout, result.stderr


class TestGitHubIssues:
    """Tests for GitHub issues functionality."""

    def test_list_issues(self):
        """Test that issues can be listed from a GitHub repository.

        Given: A valid GitHub repository
        When: The gh issue list command is executed
        Then: A list of issues is returned in JSON format
        """
        # When
        return_code, stdout, stderr = run_gh_command(
            ["issue", "list", f"--repo={OWNER}/{REPO}", "--json=number,title,state,url"]
        )

        # Then
        assert return_code == 0, f"Command failed with error: {stderr}"
        issues = json.loads(stdout)
        assert isinstance(issues, list), "Expected a list of issues"
        if issues:  # Only if there are issues
            assert "number" in issues[0], "Issue should have a number"
            assert "title" in issues[0], "Issue should have a title"
            assert "state" in issues[0], "Issue should have a state"
            assert "url" in issues[0], "Issue should have a URL"

    def test_create_view_edit_close_reopen_issue(self):
        """Test the full lifecycle of an issue: create, view, edit, close, and reopen.

        Given: A valid GitHub repository
        When: Issue commands are executed in sequence
        Then: The issue is created, can be viewed, edited, closed, and reopened
        """
        # Create an issue
        title = generate_test_data("Integration-Test")
        body = f"Test issue created by integration test at {time.ctime()}"

        # When - Create issue
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "create",
                f"--repo={OWNER}/{REPO}",
                f"--title={title}",
                f"--body={body}",
            ]
        )

        # Then - Issue created successfully
        assert return_code == 0, f"Issue creation failed: {stderr}"
        issue_url = stdout.strip()
        issue_number = int(issue_url.split("/")[-1])

        # When - View issue
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "view",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                "--json=number,title,state,url",
            ]
        )

        # Then - Issue can be viewed
        assert return_code == 0, f"Issue view failed: {stderr}"
        issue_data = json.loads(stdout)
        assert issue_data["number"] == issue_number
        assert issue_data["title"] == title
        assert issue_data["state"] == "OPEN"

        # When - Edit issue
        new_title = generate_test_data("Edited-Integration-Test")
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "edit",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                f"--title={new_title}",
            ]
        )

        # Then - Issue can be edited
        assert return_code == 0, f"Issue edit failed: {stderr}"

        # Verify edit
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "view",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                "--json=title",
            ]
        )
        issue_data = json.loads(stdout)
        assert issue_data["title"] == new_title

        # When - Close issue
        return_code, stdout, stderr = run_gh_command(
            ["issue", "close", str(issue_number), f"--repo={OWNER}/{REPO}"]
        )

        # Then - Issue can be closed
        assert return_code == 0, f"Issue close failed: {stderr}"

        # Verify closure
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "view",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                "--json=state",
            ]
        )
        issue_data = json.loads(stdout)
        assert issue_data["state"] == "CLOSED"

        # When - Reopen issue
        return_code, stdout, stderr = run_gh_command(
            ["issue", "reopen", str(issue_number), f"--repo={OWNER}/{REPO}"]
        )

        # Then - Issue can be reopened
        assert return_code == 0, f"Issue reopen failed: {stderr}"

        # Verify reopening
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "view",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                "--json=state",
            ]
        )
        issue_data = json.loads(stdout)
        assert issue_data["state"] == "OPEN"

    def test_create_issue_with_labels(self):
        """Test creating an issue with labels.

        Given: A valid GitHub repository with a 'bug' label
        When: An issue is created with the bug label
        Then: The issue has the label correctly applied
        """
        # Ensure we have a bug label - this will succeed even if it already exists
        run_gh_command(
            [
                "label",
                "create",
                "bug",
                f"--repo={OWNER}/{REPO}",
                "--description=Bug reports",
                "--color=FF0000",
                "--force",
            ]
        )

        # Create issue with label
        title = generate_test_data("Label-Test")
        body = f"Test issue with labels created at {time.ctime()}"

        # When
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "create",
                f"--repo={OWNER}/{REPO}",
                f"--title={title}",
                f"--body={body}",
                "--label=bug",
            ]
        )

        # Then
        assert return_code == 0, f"Issue creation with label failed: {stderr}"
        issue_url = stdout.strip()
        issue_number = int(issue_url.split("/")[-1])

        # Verify label was applied
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "view",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                "--json=labels",
            ]
        )

        # Then
        assert return_code == 0
        issue_data = json.loads(stdout)
        labels = [label["name"] for label in issue_data.get("labels", [])]
        assert "bug" in labels, f"Label 'bug' was not found in {labels}"

    def test_create_issue_with_assignee(self):
        """Test creating an issue with an assignee.

        Given: A valid GitHub repository and user
        When: An issue is created with an assignee
        Then: The issue has the assignee correctly applied
        """
        # Create issue with assignee
        title = generate_test_data("Assignee-Test")
        body = f"Test issue with assignee created at {time.ctime()}"

        # When
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "create",
                f"--repo={OWNER}/{REPO}",
                f"--title={title}",
                f"--body={body}",
                f"--assignee={OWNER}",
            ]
        )

        # Then
        assert return_code == 0, f"Issue creation with assignee failed: {stderr}"
        issue_url = stdout.strip()
        issue_number = int(issue_url.split("/")[-1])

        # Verify assignee was applied
        return_code, stdout, stderr = run_gh_command(
            [
                "issue",
                "view",
                str(issue_number),
                f"--repo={OWNER}/{REPO}",
                "--json=assignees",
            ]
        )

        # Then
        assert return_code == 0
        issue_data = json.loads(stdout)
        assignees = [assignee["login"] for assignee in issue_data.get("assignees", [])]
        assert OWNER in assignees, f"Assignee '{OWNER}' was not found in {assignees}"


class TestGitHubPullRequests:
    """Tests for GitHub pull requests functionality."""

    @pytest.fixture
    def test_branch(self):
        """Create a test branch for PR testing.

        This fixture creates a temporary container, clones the repository,
        creates a branch, makes a change, and pushes the branch.

        Returns
        -------
            The name of the created branch.

        """
        import subprocess

        # Create a unique branch name
        branch_name = f"test-branch-{int(time.time())}"
        container_name = f"git-test-{uuid.uuid4().hex[:8]}"

        # Start a container
        start_cmd = [
            "docker",
            "run",
            "--name",
            container_name,
            "-d",
            "-e",
            f"GH_TOKEN={GH_TOKEN}",
            DOCKER_IMAGE,
            "sleep",
            "3600",
        ]
        subprocess.run(start_cmd, capture_output=True, check=True)

        try:
            # Clone the repo
            clone_cmd = [
                "docker",
                "exec",
                "-i",
                container_name,
                "bash",
                "-c",
                f"cd /tmp && git clone https://{GH_TOKEN}@github.com/{OWNER}/{REPO}.git",
            ]
            subprocess.run(clone_cmd, capture_output=True, check=True)

            # Create a branch
            branch_cmd = [
                "docker",
                "exec",
                "-i",
                container_name,
                "bash",
                "-c",
                f"cd /tmp/{REPO} && git checkout -b {branch_name}",
            ]
            subprocess.run(branch_cmd, capture_output=True, check=True)

            # Make a change
            timestamp = int(time.time())
            change_cmd = [
                "docker",
                "exec",
                "-i",
                container_name,
                "bash",
                "-c",
                f'echo "# Test commit {timestamp}" >> /tmp/{REPO}/README.md',
            ]
            subprocess.run(change_cmd, capture_output=True, check=True)

            # Commit the change
            commit_cmd = [
                "docker",
                "exec",
                "-i",
                container_name,
                "bash",
                "-c",
                f'cd /tmp/{REPO} && git config --global user.email "test@example.com" && '
                + 'git config --global user.name "Test User" && git add README.md && '
                + f'git commit -m "Test commit {timestamp}"',
            ]
            subprocess.run(commit_cmd, capture_output=True, check=True)

            # Push the branch
            push_cmd = [
                "docker",
                "exec",
                "-i",
                container_name,
                "bash",
                "-c",
                f"cd /tmp/{REPO} && git push origin {branch_name}",
            ]
            subprocess.run(push_cmd, capture_output=True, check=True)

            # Return the branch name for use in tests
            yield branch_name

        finally:
            # Clean up the container
            cleanup_cmd = [
                "docker",
                "stop",
                container_name,
                "&&",
                "docker",
                "rm",
                container_name,
            ]
            subprocess.run(" ".join(cleanup_cmd), shell=True, capture_output=True)

    def test_list_pull_requests(self):
        """Test that pull requests can be listed from a GitHub repository.

        Given: A valid GitHub repository
        When: The gh pr list command is executed
        Then: A list of pull requests is returned in JSON format
        """
        # When
        return_code, stdout, stderr = run_gh_command(
            ["pr", "list", f"--repo={OWNER}/{REPO}", "--json=number,title,state,url"]
        )

        # Then
        assert return_code == 0, f"Command failed with error: {stderr}"
        # Even if empty, it should return a valid JSON array
        prs = json.loads(stdout)
        assert isinstance(prs, list), "Expected a list of PRs"

    def test_create_view_comment_close_pr(self, test_branch):
        """Test the lifecycle of a pull request: create, view, comment, and close.

        Given: A valid GitHub repository and a branch with changes
        When: PR commands are executed in sequence
        Then: The PR is created, can be viewed, commented on, and closed
        """
        # Create a PR
        title = generate_test_data("PR-Test")

        # When - Create PR
        return_code, stdout, stderr = run_gh_command(
            [
                "pr",
                "create",
                f"--repo={OWNER}/{REPO}",
                f"--head={test_branch}",
                "--base=main",
                f"--title={title}",
                "--body=Test PR created by integration test",
            ]
        )

        # Then - PR created successfully
        assert return_code == 0, f"PR creation failed: {stderr}"
        pr_url = stdout.strip()
        pr_number = int(pr_url.split("/")[-1])

        # When - View PR
        return_code, stdout, stderr = run_gh_command(
            [
                "pr",
                "view",
                str(pr_number),
                f"--repo={OWNER}/{REPO}",
                "--json=number,title,state,url",
            ]
        )

        # Then - PR can be viewed
        assert return_code == 0, f"PR view failed: {stderr}"
        pr_data = json.loads(stdout)
        assert pr_data["number"] == pr_number
        assert pr_data["title"] == title
        assert pr_data["state"] == "OPEN"

        # When - Comment on PR
        comment_body = generate_test_data("PR-Comment")
        return_code, stdout, stderr = run_gh_command(
            [
                "pr",
                "comment",
                str(pr_number),
                f"--repo={OWNER}/{REPO}",
                f"--body={comment_body}",
            ]
        )

        # Then - Comment added successfully
        assert return_code == 0, f"PR comment failed: {stderr}"
        assert stdout.strip().startswith("https://"), "Expected a URL for the comment"

        # When - Close PR
        return_code, stdout, stderr = run_gh_command(
            ["pr", "close", str(pr_number), f"--repo={OWNER}/{REPO}"]
        )

        # Then - PR closed successfully
        assert return_code == 0, f"PR close failed: {stderr}"

        # Verify PR is closed
        return_code, stdout, stderr = run_gh_command(
            ["pr", "view", str(pr_number), f"--repo={OWNER}/{REPO}", "--json=state"]
        )
        pr_data = json.loads(stdout)
        assert (
            pr_data["state"] == "CLOSED"
        ), f"PR state is {pr_data['state']}, not CLOSED"
