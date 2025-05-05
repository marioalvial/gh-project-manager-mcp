"""GitHub Project Manager MCP tools package."""

import inspect
from typing import Any, Dict

# Export modules
__all__ = ["issues", "pull_requests"]


def tool_registry_info() -> Dict[str, Any]:
    """Return information about registered tools for diagnostic purposes.

    This can be called from the console or diagnostic endpoints
    to verify if the tools were registered correctly.

    Returns
    -------
        Dict with tool registration information

    """
    info = {"discovery": {}, "registered_tools": []}

    # Try to inspect the FastMCP module to find registered tools
    try:
        # Get server instance - for diagnostic only
        from gh_project_manager_mcp.server import server

        if hasattr(server, "_mcp_server"):
            mcp_server = server._mcp_server
            info["discovery"]["server_found"] = True

            # Try to access registered tools
            if hasattr(mcp_server, "_tool_handlers"):
                handlers = mcp_server._tool_handlers
                info["discovery"]["handlers_found"] = True
                info["discovery"]["handler_count"] = len(handlers)

                # List registered tools
                for name, handler in handlers.items():
                    tool_info = {
                        "name": name,
                        "function": str(handler),
                        "signature": str(inspect.signature(handler))
                        if callable(handler)
                        else None,
                    }
                    info["registered_tools"].append(tool_info)
    except Exception as e:
        info["discovery"]["error"] = str(e)

    return info


def discover_tools() -> Dict[str, Any]:
    """Discover all tool functions registered in this package.

    Introspect modules to identify tool functions designed
    to be registered with the FastMCP server.

    Returns
    -------
        Information about the discovered tool functions

    """
    info = {"discovery": {}, "registered_tools": []}

    # Get all module level functions
    module_funcs = {}
    for name, obj in globals().items():
        if inspect.isfunction(obj) and inspect.getmodule(obj) == inspect.getmodule(
            discover_tools
        ):
            module_funcs[name] = obj

    info["discovery"] = {
        "module_functions": list(module_funcs.keys()),
    }

    return info
