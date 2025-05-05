"""Handle errors for the GitHub Project Manager MCP server."""

import traceback
from enum import Enum
from typing import Any, Dict, Optional

from result import Err, Ok, Result


class ErrorCode(Enum):
    """Define error codes for the application."""

    GH_TOKEN_NOT_FOUND = "GitHub token not found in environment"
    GH_COMMAND_FAILED = "GitHub CLI command failed: {reason}"
    GH_CLI_NOT_FOUND = "GitHub CLI not found"
    GH_UNEXPECTED_ERROR = "Unexpected error: {message}"
    CONFIG_PARAM_NOT_FOUND = "Config param '{param}' not found in category {category}"
    REQUIRED_PARAM_MISSING = "Required parameter '{param}' is missing"
    REQUIRED_PARAMS_MISSING = "Required parameters {params} are missing"
    INVALID_PARAM = "Invalid parameter '{param}'. Must be one of: {valid_params}"

    def format(self, **kwargs) -> str:
        """Format the error message template with provided parameters."""
        return self.value.format(**kwargs)


class Error:
    """Represent a generic error response."""

    def __init__(
        self,
        code: ErrorCode,
        exception: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
        format_args: Optional[Dict[str, Any]] = None,
    ):
        """Initialize an error with code and optional details.

        Args:
        ----
            code: The error code
            exception: Original exception that caused this error (optional)
            details: Additional error details
            format_args: Arguments for formatting the error message template

        """
        self.status = "FAILED"
        self.code = code
        self.exception = exception
        self.details = details

        # Format message if format_args provided, otherwise use template
        if format_args:
            self.message = code.format(**format_args)
        else:
            self.message = code.value

    def __str__(self) -> str:
        """Convert error to a readable string representation.

        Returns
        -------
            str: A human-readable error message string

        """
        result = f"Error: {self.message}"

        if self.details:
            details_str = ", ".join(f"{k}: {v}" for k, v in self.details.items())
            result += f" | Details: {details_str}"

        if self.exception:
            exc_str = str(self.exception)
            if exc_str:
                result += f" | Exception: {exc_str}"

        return result

    def __repr__(self) -> str:
        """Return a programmer-readable string representation.

        Returns
        -------
            str: String representation for debugging

        """
        return f"Error(code={self.code.name}, message='{self.message}')"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for JSON serialization.

        Returns
        -------
            Dict[str, Any]: Dictionary representation of the error

        """
        result = {
            "status": self.status,
            "code": self.code.name,
            "message": self.message,
        }

        if self.details:
            result["details"] = self.details

        if self.exception:
            result["exception"] = str(self.exception)

        return result

    @staticmethod
    def required_param_missing(param: str) -> "Error":
        """Create an error for a missing required parameter.

        Args:
        ----
            param: The name of the required parameter that is missing

        Returns:
        -------
            Error: A configured Error instance

        """
        return Error(
            ErrorCode.REQUIRED_PARAM_MISSING,
            format_args={"param": param},
        )

    @staticmethod
    def required_params_missing(params: list[str]) -> "Error":
        """Create an error for missing required parameters.

        Args:
        ----
            params: List of required parameters that are missing

        Returns:
        -------
            Error: A configured Error instance

        """
        return Error(
            ErrorCode.REQUIRED_PARAMS_MISSING,
            format_args={"params": ", ".join(params)},
        )

    @staticmethod
    def config_param_not_found(param: str, category: str) -> "Error":
        """Create an error for a missing configuration parameter.

        Args:
        ----
            param: The name of the missing parameter
            category: The category of the missing parameter

        Returns:
        -------
            Error: A configured Error instance

        """
        return Error(
            ErrorCode.CONFIG_PARAM_NOT_FOUND,
            format_args={"param": param, "category": category},
        )

    @staticmethod
    def invalid_param(
        param: str, valid_params: list[str], message: Optional[str] = None
    ) -> "Error":
        """Create an error for an invalid parameter.

        Args:
        ----
            param: The name of the invalid parameter
            valid_params: List of valid parameters
            message: Optional custom error message

        Returns:
        -------
            Error: A configured Error instance

        """
        error = Error(
            ErrorCode.INVALID_PARAM,
            format_args={"param": param, "valid_params": ", ".join(valid_params)},
        )

        if message:
            error.details = {"message": message}

        return error

    @classmethod
    def from_exception(cls, exception: Exception) -> "Error":
        """Create an error instance from just an exception.

        A simplified constructor that creates an Error with the GH_UNEXPECTED_ERROR code
        and uses the exception's string representation as the message.

        Args:
        ----
            exception: The exception to create an error from

        Returns:
        -------
            Error: A configured Error instance

        """
        return cls(
            code=ErrorCode.GH_UNEXPECTED_ERROR,
            exception=exception,
            details={"traceback": traceback.format_exc()},
            format_args={"message": str(exception) or "An unexpected error occurred"},
        )


class ApplicationError(Exception):
    """Wrap our Error object for application-wide error handling."""

    def __init__(self, error: Error):
        """Initialize an ApplicationError.

        Args:
        ----
            error: The Error object to wrap.

        """
        self.error = error
        super().__init__(error.message)


def validate_required_param(param_name: str, param_value: Any) -> Result[Any, Error]:
    """Validate that a required parameter has a value.

    Args:
    ----
        param_name: Name of the parameter to validate
        param_value: Value to check

    Returns:
    -------
        Ok with the parameter value if it's not None
        Err with an error if it's None

    """
    if param_value is None:
        return Err(
            Error(ErrorCode.CONFIG_PARAM_NOT_FOUND, format_args={"param": param_name})
        )
    return Ok(param_value)
