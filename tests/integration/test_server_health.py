#!/usr/bin/env python3
"""Test script for GitHub Project Manager MCP server health check."""

import pytest
import requests

# MCP server details
MCP_SERVER_URL = "http://localhost:8191"


def test_server_health():
    """Test that the MCP server is running and healthy."""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health")
        response.raise_for_status()  # Raise an exception for HTTP errors

        # If we get here, the server is running and healthy
        assert response.status_code == 200
        assert response.text.strip() == "OK"
        print("Server health check passed")

    except requests.exceptions.ConnectionError:
        pytest.skip("MCP server is not running on localhost:8191")
    except Exception as e:
        pytest.fail(f"Server health check failed: {e}")


if __name__ == "__main__":
    print("Testing GitHub Project Manager MCP Server Health")
    print("==============================================")
    test_server_health()
