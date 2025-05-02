# tests/test_config.py
"""Tests for the TOOL_PARAM_CONFIG structure and completeness."""

import re
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any

import pytest

from gh_project_manager_mcp.config import TOOL_PARAM_CONFIG


@pytest.fixture
def resolve_param_calls() -> List[Tuple[str, str]]:
    """Find all resolve_param calls in tool implementation files.
    
    Returns:
        List[Tuple[str, str]]: A list of tuples, each containing (capability_str, param_name_str).
    """
    tools_dir = Path("src/gh_project_manager_mcp/tools")
    checked_params: Set[Tuple[str, str]] = set()

    for tool_file in tools_dir.glob("*.py"):
        if tool_file.name == "__init__.py":
            continue

        file_content = tool_file.read_text()
        found_params = _find_resolve_param_calls(file_content)
        checked_params.update(found_params)
    
    return list(checked_params)


def _find_resolve_param_calls(file_content: str) -> List[Tuple[str, str]]:
    """Find all calls to resolve_param in the given file content.

    Args:
        file_content: The string content of the Python file.

    Returns:
        A list of tuples, each containing (capability_str, param_name_str).
    """
    # Regex to find resolve_param('capability', 'param_name', ...)
    # It captures the first two string arguments (capability and param_name)
    pattern = re.compile(
        r"""
        resolve_param\(\s*            # Match 'resolve_param(' and optional whitespace
        ['"]([^\'"]+)['"]\s*,\s*      # Capture the first string literal (capability)
        ['"]([^\'"]+)['"]             # Capture the second string literal (param_name)
        # We don't need to match the rest of the arguments
    """,
        re.VERBOSE,
    )
    matches = pattern.findall(file_content)
    # Return list of (capability, param_name) tuples
    return [(cap.strip(), name.strip()) for cap, name in matches]


class TestConfigCompleteness:
    """Tests for verifying the completeness of configuration definitions."""
    
    def test_tool_param_config_completeness(self, resolve_param_calls: List[Tuple[str, str]]) -> None:
        """Verify parameters used with resolve_param have 'type' in config.
        
        Given: All resolve_param calls collected from tool implementation files
        When: Checking each capability/parameter combination against TOOL_PARAM_CONFIG
        Then: Every parameter present in TOOL_PARAM_CONFIG should have a 'type' key
        """
        # Given
        missing_params: List[str] = []
        
        # When
        for capability, param_name in resolve_param_calls:
            capability_config = TOOL_PARAM_CONFIG.get(capability)
            if capability_config is not None:
                param_config = capability_config.get(param_name)
                if param_config is not None:
                    # Only check for 'type' if the param exists in the config
                    if "type" not in param_config:
                        missing_params.append(
                            f"""Parameter '{param_name}' under capability '{capability}' \
    is missing the 'type' key in TOOL_PARAM_CONFIG."""
                        )
            # No error if capability or param_name is not found in config,
            # as resolve_param handles this.
    
        # Then
        assert (
            not missing_params
        ), (
            "Parameters found in TOOL_PARAM_CONFIG are missing the 'type' key:\n"
            + "\n".join(missing_params)
        )
    
    def test_tool_param_config_structure(self) -> None:
        """Verify TOOL_PARAM_CONFIG has the expected structure.
        
        Given: The TOOL_PARAM_CONFIG dictionary
        When: Examining its structure
        Then: Each capability should have parameters
              Each parameter should have at least a 'type' key
        """
        # Given
        invalid_entries: List[str] = []
        
        # When
        for capability, params in TOOL_PARAM_CONFIG.items():
            if not isinstance(params, dict):
                invalid_entries.append(f"Capability '{capability}' is not a dictionary")
                continue
                
            for param_name, param_config in params.items():
                if not isinstance(param_config, dict):
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability '{capability}' is not a dictionary"
                    )
                    continue
                    
                if "type" not in param_config:
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability '{capability}' is missing 'type' key"
                    )
                
                # Validate type value is one of the expected types
                if param_config.get("type") not in ["str", "int", "list", "bool"]:
                    invalid_entries.append(
                        f"Parameter '{param_name}' in capability '{capability}' has invalid type: {param_config.get('type')}"
                    )
        
        # Then
        assert not invalid_entries, (
            "TOOL_PARAM_CONFIG has structure issues:\n" + "\n".join(invalid_entries)
        )
