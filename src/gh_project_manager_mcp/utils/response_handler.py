"""Handle function results and convert them to JSON responses."""

import functools
from typing import Any, Callable, Dict, Generic, Protocol, TypeVar

from result import Ok, Result

from gh_project_manager_mcp.utils.error import Error
from gh_project_manager_mcp.utils.gh_utils import print_stderr

T = TypeVar("T")
E = TypeVar("E")  # Error type


# Define a protocol for functions that return Result
class ResultReturningCallable(Protocol, Generic[T, E]):
    """Protocol for functions that return Result objects."""

    def __call__(self, *args: Any, **kwargs: Any) -> Result[T, E]: ...


def _format_success_response(value: Any) -> Dict[str, Any]:
    """Format a successful result as a standardized JSON response.

    Args:
    ----
        value: The success value to format

    Returns:
    -------
        A standardized JSON-serializable dictionary

    """
    # Check if value is a string that might be JSON
    if isinstance(value, str):
        try:
            # Try to parse it as JSON
            import json

            parsed_value = json.loads(value)
            # If parsing succeeds, use the parsed object
            return {"status": "SUCCESS", "raw": parsed_value}
        except json.JSONDecodeError:
            # If it's not valid JSON, use the original string
            pass

    # Default case: use the value as is
    return {"status": "SUCCESS", "raw": value}


def _format_error_response(error: Any) -> Dict[str, Any]:
    """Format an error result as a standardized JSON response.

    Args:
    ----
        error: The error value to format

    Returns:
    -------
        A standardized JSON-serializable dictionary

    """
    # If the error is already an Error object, convert it to dict
    if isinstance(error, Error):
        return error.to_dict()

    # If it's already a dict, return it
    if isinstance(error, dict) and "status" in error:
        return error

    # Otherwise wrap it in a generic error format
    return {"status": "FAILED", "code": "UNKNOWN_ERROR", "message": str(error)}


def handle_result(func: ResultReturningCallable[T, E]) -> Callable[..., Dict[str, Any]]:
    """Process Results and convert them directly to JSON-serializable dictionaries.

    This decorator standardizes the format of successful and error responses
    from functions that return Result objects, and returns a JSON-ready dictionary
    instead of a Result object.

    Args:
    ----
        func: The function to wrap (must return Result)

    Returns:
    -------
        A wrapped function that returns JSON-ready dictionaries directly

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Call the function and return JSON-serializable response.

        Args:
        ----
            *args: Arguments to pass to the wrapped function
            **kwargs: Keyword arguments to pass to the wrapped function

        Returns:
        -------
            A JSON-serializable dictionary with standardized format

        """
        try:
            # Call the original function
            result = func(*args, **kwargs)

            # Process the result
            if isinstance(result, Ok):
                # Format successful result
                return _format_success_response(result.unwrap())
            else:  # isinstance(result, Err)
                # Format error result
                error_value = result.err_value
                return _format_error_response(error_value)

        except Exception as e:
            # Create an Error object from the exception
            error = Error.from_exception(e)
            print_stderr(f"ERROR in {func.__name__}: {e}")

            # Return formatted error
            return _format_error_response(error)

    # Type casting is only for static type checkers
    return wrapper
