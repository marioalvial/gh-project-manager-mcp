"""Main entry point for the GitHub Project Manager MCP server."""

import json
import os

import uvicorn

# from mcp import FastMCP
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse

from gh_project_manager_mcp.tools import issues as issue_tools
from gh_project_manager_mcp.tools import pull_requests as pr_tools

# Commented out until implemented
# from gh_project_manager_mcp.tools import projects as project_tools
from gh_project_manager_mcp.utils import gh_utils


# Middleware para logar todas as requisições
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Log da requisição recebida
        print(f"DEBUG [HTTP]: {request.method} {request.url.path}")

        # Para requests POST, tenta ler e logar o corpo da requisição
        if request.method == "POST":
            try:
                body_bytes = await request.body()
                try:
                    # Tenta analisar como JSON se possível
                    body_json = json.loads(body_bytes)
                    print(f"DEBUG [HTTP Body]: {json.dumps(body_json)[:500]}")
                except json.JSONDecodeError:
                    # Caso contrário, mostra os bytes brutos
                    print(f"DEBUG [HTTP Body Raw]: {body_bytes[:200]}")
            except Exception as e:
                print(f"DEBUG [HTTP Error]: Failed to read request body: {str(e)}")

        # Continua com o processamento normal da requisição
        response = await call_next(request)

        # Log da resposta
        print(f"DEBUG [HTTP Response]: Status {response.status_code}")
        return response


# Simple health check endpoint - KEEP
async def health(request):
    """Run simple health check."""
    print("DEBUG [Health]: Health check request received")
    return PlainTextResponse("OK")


def main():
    """Initialize and start the MCP server.

    This function creates a FastMCP instance, registers tools from different modules,
    and returns the configured server instance.

    Returns
    -------
        FastMCP: The initialized server instance

    """
    print("Registering tools...")

    # Check for GitHub token and exit if not found
    token = gh_utils.get_github_token()
    if not token:
        print("Error: GitHub token not found in environment.")
        print("       Please set GITHUB_TOKEN or GH_TOKEN environment variable.")
        import sys

        sys.exit(1)
    else:
        print("Found GitHub token, proceeding with startup.")

    # Create the server instance
    server = FastMCP(
        title="GitHub Project Manager MCP",
        description="An MCP server wrapping the GitHub CLI (`gh`) "
        "for project management tasks.",
        version="0.1.0",
    )

    # Initialize tools from different modules
    issue_tools.init_tools(server)
    pr_tools.init_tools(server)
    # project_tools.init_tools(server) # Uncomment when ready

    print("Tool registration complete.")

    # Return the server for testing purposes
    return server


if __name__ == "__main__":
    # Get host and port from env vars for informational purposes
    host = os.environ.get("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_SERVER_PORT", 8191))
    print(f"Starting server on host {host}, port {port}...")

    # Using the official MCP SDK approach with SSE transport
    server = main()

    from starlette.applications import Starlette

    # Remove unused imports if info/home are removed
    # from starlette.responses import HTMLResponse, JSONResponse # Removed these
    from starlette.routing import Route

    # REMOVED info async function

    # REMOVED home async function

    # Create and configure the SSE transport with correct endpoints - KEEP
    sse = SseServerTransport("/messages")  # Removido o trailing slash

    # SSE connection handler - KEEP
    async def handle_sse(request: Request) -> None:
        """Handle incoming SSE connections."""
        print("DEBUG [SSE]: New SSE connection received")
        try:
            # Adiciona um ID de sessão fake para diagnóstico, se não estiver presente
            if "session_id" not in request.query_params:
                print(
                    "DEBUG [SSE]: No session_id in query params, this might cause issues"
                )
            else:
                print(
                    f"DEBUG [SSE]: Session ID from query params: {request.query_params['session_id']}"
                )

            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
            ) as (read_stream, write_stream):
                print("DEBUG [SSE]: SSE connection established successfully")
                # Run the MCP server with the streams
                # Use server's initialization options
                initialization_options = (
                    server._mcp_server.create_initialization_options()
                )
                print(
                    f"DEBUG [SSE]: Server initialization options: {initialization_options}"
                )

                try:
                    await server._mcp_server.run(
                        read_stream,
                        write_stream,
                        initialization_options,
                    )
                    print("DEBUG [SSE]: MCP server run completed normally")
                except Exception as e:
                    import traceback

                    print(f"DEBUG [SSE ERROR]: MCP server run failed: {str(e)}")
                    print(f"DEBUG [SSE ERROR]: Traceback: {traceback.format_exc()}")
        except Exception as e:
            import traceback

            print(f"DEBUG [SSE CONNECTION ERROR]: {str(e)}")
            print(f"DEBUG [SSE CONNECTION ERROR]: Traceback: {traceback.format_exc()}")

    # Vamos adicionar um manipulador de diagnóstico MCP para rastrear e investigar
    async def direct_mcp_handler(request: Request) -> None:
        """Um manipulador direto para comunicação MCP para diagnóstico."""
        print("DEBUG [Direct MCP]: Request received")
        try:
            # Tenta ler e analisar o corpo da requisição para diagnóstico
            body_bytes = await request.body()
            try:
                if body_bytes:
                    body_json = json.loads(body_bytes)
                    print(
                        f"DEBUG [Direct MCP]: Request JSON: {json.dumps(body_json)[:500]}"
                    )

                    # Se for uma solicitação de ferramenta create_github_issue_impl
                    if (
                        "type" in body_json
                        and body_json["type"] == "request"
                        and "params" in body_json
                        and "handlerName" in body_json["params"]
                        and body_json["params"]["handlerName"]
                        == "_create_github_issue_impl"
                        and "arguments" in body_json["params"]
                    ):
                        args = body_json["params"]["arguments"]
                        print(f"DEBUG [Direct MCP]: Tool arguments: {args}")

                        # Extrair os parâmetros necessários
                        owner = args.get("owner")
                        repo = args.get("repo")
                        title = args.get("title")

                        # Validar que temos todos os parâmetros obrigatórios
                        if not all([owner, repo, title]):
                            print(
                                f"DEBUG [Direct MCP]: Missing required parameters. owner={owner}, repo={repo}, title={title}"
                            )
                            return JSONResponse(
                                {
                                    "error": "Missing required parameters",
                                    "required": ["owner", "repo", "title"],
                                    "received": args,
                                },
                                status_code=400,
                            )

                        # Chamar a função diretamente
                        from gh_project_manager_mcp.tools.issues import (
                            _create_github_issue_impl,
                        )

                        result = _create_github_issue_impl(
                            owner=owner, repo=repo, title=title
                        )

                        # Montar a resposta de acordo com o protocolo MCP
                        mcp_response = {
                            "type": "response",
                            "id": body_json.get("id", "unknown"),
                            "result": result,
                        }
                        if "session_id" in body_json:
                            mcp_response["session_id"] = body_json["session_id"]

                        print(
                            f"DEBUG [Direct MCP]: Response: {json.dumps(mcp_response)[:500]}"
                        )
                        return JSONResponse(mcp_response)
            except json.JSONDecodeError:
                print("DEBUG [Direct MCP]: Not a valid JSON")
            except Exception as e:
                import traceback

                print(f"DEBUG [Direct MCP]: Error processing request: {str(e)}")
                print(f"DEBUG [Direct MCP]: Traceback: {traceback.format_exc()}")
        except Exception as e:
            import traceback

            print(f"DEBUG [Direct MCP]: Error reading request: {str(e)}")
            print(f"DEBUG [Direct MCP]: Traceback: {traceback.format_exc()}")

        # Se não conseguimos processar de forma especial, continuar com o processamento normal SSE
        return await sse.handle_post_message(request)

    # Adicionar um endpoint direto para diagnóstico
    async def direct_create_issue(request: Request):
        """Endpoint de diagnóstico para criar issues diretamente."""
        print("DEBUG [Direct Create Issue]: Request received")
        try:
            # Extrai os parâmetros da query ou do corpo
            if request.method == "GET":
                params = dict(request.query_params)
            else:
                try:
                    body = await request.json()
                    params = body
                except:
                    body_bytes = await request.body()
                    params = {"raw_body": body_bytes.decode("utf-8", errors="replace")}

            print(f"DEBUG [Direct Create Issue]: Parameters: {params}")

            # Extrai os parâmetros necessários
            owner = params.get("owner", "marioalvial")
            repo = params.get("repo", "gh-project-manager-mcp")
            title = params.get("title", "Test Issue via Direct Endpoint")

            # Importa e chama a função diretamente
            from gh_project_manager_mcp.tools.issues import _create_github_issue_impl

            print(
                f"DEBUG [Direct Create Issue]: Calling with owner={owner}, repo={repo}, title={title}"
            )
            result = _create_github_issue_impl(owner=owner, repo=repo, title=title)

            # Retorna o resultado como JSON
            print(f"DEBUG [Direct Create Issue]: Result: {result}")
            return JSONResponse(result)
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            print(f"DEBUG [Direct Create Issue]: Error: {str(e)}")
            print(f"DEBUG [Direct Create Issue]: Traceback: {error_trace}")
            return JSONResponse(
                {
                    "error": "Exception in direct_create_issue",
                    "details": str(e),
                    "traceback": error_trace,
                },
                status_code=500,
            )

    # Create a starlette app - REMOVE '/' and '/info' routes
    app = Starlette(
        routes=[
            # Route("/", home), # REMOVED
            Route("/health", health),  # KEEP
            # Route("/info", info), # REMOVED
            # Direct SSE connection endpoint com suporte a POST para o MCP client
            Route("/sse", endpoint=handle_sse, methods=["GET"]),  # Para GET (eventos)
            Route(
                "/sse", endpoint=direct_mcp_handler, methods=["POST"]
            ),  # Para POST (comandos)
            # Endpoint /messages com método POST especificado para o direct_mcp_handler
            Route("/messages", endpoint=direct_mcp_handler, methods=["POST"]),
            # Um endpoint independente que usa o handler SSE diretamente (para testes)
            Route("/raw-messages", endpoint=sse.handle_post_message, methods=["POST"]),
            # Adicionar endpoint direto para diagnóstico de criação de issues
            Route(
                "/direct-create-issue",
                endpoint=direct_create_issue,
                methods=["GET", "POST"],
            ),
        ],
        middleware=[
            # Adicionar o middleware de logging
            # Middleware precisa ser instanciado APÓS o app ser criado
            Middleware(RequestLoggingMiddleware),
        ],
    )

    # Run uvicorn with the app and configured host/port - KEEP
    uvicorn.run(app, host=host, port=port)
