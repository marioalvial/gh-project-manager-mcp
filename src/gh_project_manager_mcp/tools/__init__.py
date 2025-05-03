"""Tool modules for implementing GitHub CLI functionality."""

# This file can be empty

"""Tool modules initialization."""

# Import modules so they can be imported as a group
import inspect
import json
from typing import Any, Dict, List, Optional

# Functions to help with tool registration diagnosis


def tool_registry_info() -> Dict[str, Any]:
    """Retorna informações sobre ferramentas registradas para diagnóstico.

    Isto pode ser chamado do console ou de endpoints de diagnóstico
    para verificar se as ferramentas foram registradas corretamente.
    """
    from mcp.server.fastmcp import FastMCP

    info = {"discovery": {}, "registered_tools": []}

    # Tenta inspecionar o módulo FastMCP para encontrar as ferramentas registradas
    try:
        # Apenas para diagnóstico - não é uma forma robusta de acessar
        # dados privados, mas útil para debug
        from gh_project_manager_mcp.server import server

        if hasattr(server, "_mcp_server"):
            mcp_server = server._mcp_server
            info["discovery"]["server_found"] = True

            # Tenta acessar ferramentas registradas
            if hasattr(mcp_server, "_tool_handlers"):
                handlers = mcp_server._tool_handlers
                info["discovery"]["handlers_found"] = True
                info["discovery"]["handler_count"] = len(handlers)

                # Lista as ferramentas registradas
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
