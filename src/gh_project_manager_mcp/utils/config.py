"""Configuration management for the GitHub Project Manager MCP server."""

import os
from typing import Any, Dict, Optional, TypedDict

from gh_project_manager_mcp.utils.gh_utils import print_stderr

from .error import ApplicationError, Error


class ParamConfig(TypedDict):
    """Type definition for parameter configuration."""

    default: Any
    env_var: str
    type: str


class ConfigStore:
    """Configuration store for parameter defaults and environment overrides."""

    def __init__(self):
        """Initialize the configuration store."""
        self._config: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    def initialize(self):
        """Initialize configuration with defaults and environment overrides."""
        if self._initialized:
            return

        # Default configuration for all parameter categories
        defaults: Dict[str, Dict[str, ParamConfig]] = {
            "global": {
                "owner": {
                    "default": None,
                    "env_var": "GH_REPO_OWNER",
                    "type": "str",
                },
                "repo": {
                    "default": None,
                    "env_var": "GH_REPO_NAME",
                    "type": "str",
                },
            },
            "issue": {
                "body": {
                    "default": "Created via GH Project Manager MCP",
                    "env_var": "GH_ISSUE_BODY",
                    "type": "str",
                },
                "assignee": {
                    "default": "@me",
                    "env_var": "GH_ISSUE_ASSIGNEE",
                    "type": "str",
                },
                "labels": {"default": [], "env_var": "GH_ISSUE_LABELS", "type": "list"},
                "project": {
                    "default": None,
                    "env_var": "GH_ISSUE_PROJECT",
                    "type": "str",
                },
                "issue_list_limit": {
                    "default": 100,
                    "env_var": "GH_ISSUE_LIST_LIMIT",
                    "type": "int",
                },
            },
            # Add pull_request category with approved parameters
            "pull_request": {
                "body": {
                    "default": "Created via GH Project Manager MCP",
                    "env_var": "GH_PR_BODY",
                    "type": "str",
                },
                "assignee": {
                    "default": "@me",
                    "env_var": "GH_PR_ASSIGNEE",
                    "type": "str",
                },
                "base": {
                    "default": "main",
                    "env_var": "GH_PR_BASE_BRANCH",
                    "type": "str",
                },
            },
            # Add project category with all parameters used in projects.py
            "project": {
                "project_id": {
                    "default": None,
                    "env_var": "GH_PROJECT_ID",
                    "type": "str",
                },
                "project_node_id": {
                    "default": None,
                    "env_var": "GH_PROJECT_NODE_ID",
                    "type": "str",
                },
                "field_list_limit": {
                    "default": 100,
                    "env_var": "GH_PROJECT_FIELD_LIST_LIMIT",
                    "type": "int",
                },
                "item_list_limit": {
                    "default": 100,
                    "env_var": "GH_PROJECT_ITEM_LIST_LIMIT",
                    "type": "int",
                },
            },
        }

        # Initialize configuration with defaults and environment overrides
        for category, params in defaults.items():
            self._config[category] = {}

            for param_name, config in params.items():
                # Start with default value
                value: Any = config["default"]

                # Override with environment variable if present
                if config.get("env_var") and config["env_var"] in os.environ:
                    env_value: str = os.environ[config["env_var"]]
                    param_type: str = config.get("type", "str")

                    try:
                        # Convert value based on type
                        if param_type == "list" and isinstance(env_value, str):
                            value = [
                                item.strip()
                                for item in env_value.split(",")
                                if item.strip()
                            ]
                        elif param_type == "int" and isinstance(env_value, str):
                            value = int(env_value)
                        elif param_type == "bool" and isinstance(env_value, str):
                            value = env_value.lower() in ("true", "yes", "1", "t", "y")
                        elif param_type == "str":
                            value = env_value
                        else:
                            # Default to string if type not recognized
                            print_stderr(
                                f"WARNING: Unknown parameter type: {param_type}, using as string"
                            )
                            value = env_value
                    except (ValueError, TypeError) as e:
                        # Log the error but continue with default value
                        print_stderr(
                            f"ERROR: Failed to convert env var {config['env_var']} "
                            f"value '{env_value}' to type {param_type}: {str(e)}"
                        )
                        print_stderr(f"Using default value: {value}")

                # Store the resolved value
                self._config[category][param_name] = value

        self._initialized = True

    def get_value(self, category: str, param_name: str) -> Any:
        """Get value from config store.

        Args:
        ----
            category: The parameter category (e.g., "global", "issue")
            param_name: The name of the parameter to retrieve

        Returns:
        -------
            The parameter value from the configuration

        Raises:
        ------
            ApplicationError: If category or parameter doesn't exist

        """
        print_stderr(
            f"CONFIG: Attempting to get param '{param_name}' from category '{category}'"
        )

        if not self._initialized:
            self.initialize()

        if category not in self._config:
            error = Error.config_param_not_found(
                param=category,
                category=category,
            )
            raise ApplicationError(error)

        if param_name not in self._config[category]:
            error = Error.config_param_not_found(
                param=param_name,
                category=category,
            )
            raise ApplicationError(error)

        value = self._config[category][param_name]

        return value


# Create singleton instance of the ConfigStore
config_store = ConfigStore()


def resolve_param(
    category: str, param_name: str, runtime_value: Optional[Any] = None
) -> Any:
    """Resolve parameter value from runtime or config store.

    Priority:
    1. Runtime value (if not None)
    2. Value from config store (from env var or default)

    Args:
    ----
        category: Parameter category (e.g., "global", "issue", "pull_request")
        param_name: Parameter name
        runtime_value: Value provided at runtime

    Returns:
    -------
        Resolved parameter value

    Raises:
    ------
        ApplicationError: If the parameter cannot be resolved from either source

    """
    # If runtime value is provided, use it
    if runtime_value is not None:
        return runtime_value

    return config_store.get_value(category, param_name)
