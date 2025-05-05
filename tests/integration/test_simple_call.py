"""Simple direct function call test for create_issue function."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from gh_project_manager_mcp.tools.issues import create_issue
from result import Ok


def test_create_issue_direct_call():
    """Test create_issue function by calling it directly."""
    # Set environment variables needed for the function
    os.environ["GH_TOKEN"] = "dummy-token-for-test"

    # Call the function directly
    result = create_issue(
        title="Test Issue via Direct Function Call",
        owner="test-owner",
        repo="test-repo",
    )

    # Check the log file
    log_file_path = "/tmp/create_issue_simple_log.txt"
    assert os.path.exists(log_file_path), "Log file was not created"

    # Read and print the log file content
    with open(log_file_path, "r") as f:
        log_content = f.read()
        print(f"Log file content: {log_content}")

    # Assert we got a success result
    assert isinstance(result, Ok), f"Expected Ok result, got {type(result)}"
    assert "Test successful" in result.value, f"Unexpected result value: {result.value}"


if __name__ == "__main__":
    # Call the test function directly
    test_create_issue_direct_call()
    print("Test completed successfully!")
