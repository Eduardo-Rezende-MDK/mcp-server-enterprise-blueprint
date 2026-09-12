"""Serverless Entrypoint for Cloudflare Workers in Native Python.

Exposes the MCP Enterprise Server deterministically over HTTP and JSON-RPC 2.0.
"""

import json
from datetime import datetime, timezone
from js import Headers, Response

from mcp_server.registry import TOOL_DEFINITIONS
from mcp_server.schemas.calc import CalcInput
from mcp_server.schemas.hello import HelloInput
from mcp_server.tools.calc import execute_calc
from mcp_server.tools.discover import execute_discover
from mcp_server.tools.hello import execute_hello


def create_cors_headers() -> Headers:
    """Cria os cabeçalhos padrão para habilitar CORS universal."""
    headers = Headers.new()
    headers.set("Access-Control-Allow-Origin", "*")
    headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, x-mcp-version")
    headers.set("Content-Type", "application/json; charset=utf-8")
    return headers


def format_mcp_tools_list():
    """Formata o catálogo de ferramentas no padrão oficial do protocolo MCP."""
    tools = []
    for tool in TOOL_DEFINITIONS:
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "outputSchema": tool.outputSchema,
            "documentation": tool.documentation.model_dump(),
        })
    return tools


async def on_fetch(request, env):
    """Handler principal de requisições HTTP do Cloudflare Worker."""
    method = request.method
    url = request.url

    # 1. Tratar preflight CORS (OPTIONS)
    if method == "OPTIONS":
        return Response.new("", status=204, headers=create_cors_headers())

    headers = create_cors_headers()

    # 2. Rota de Health Check / Info (GET)
    if method == "GET":
        info_payload = {
            "status": "online",
            "server": "mcp-server-enterprise",
            "version": "1.0.0",
            "runtime": "Cloudflare Workers Python (Pyodide Edge)",
            "protocolVersion": "2024-11-05",
            "tools_count": len(TOOL_DEFINITIONS),
            "tools": ["discover", "hello", "calc"],
            "endpoints": {
                "rpc": "POST / (JSON-RPC 2.0)",
                "sse": "GET /sse (Server-Sent Events)",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return Response.new(json.dumps(info_payload, indent=2, ensure_ascii=False), status=200, headers=headers)

    # 3. Rota de Processamento JSON-RPC 2.0 (POST)
    if method == "POST":
        try:
            body_text = await request.text()
            if not body_text:
                return Response.new(
                    json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Corpo da requisição vazio"}}),
                    status=400,
                    headers=headers,
                )

            rpc_request = json.loads(body_text)
            rpc_id = rpc_request.get("id")
            rpc_method = rpc_request.get("method")
            params = rpc_request.get("params", {})

            # 3.1. Handshake: initialize
            if rpc_method == "initialize":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": False},
                            "logging": {},
                        },
                        "serverInfo": {
                            "name": "mcp-server-enterprise",
                            "version": "1.0.0",
                        },
                    },
                }
                return Response.new(json.dumps(response_data, ensure_ascii=False), status=200, headers=headers)

            # 3.2. Notificação: notifications/initialized
            if rpc_method == "notifications/initialized":
                return Response.new("", status=204, headers=headers)

            # 3.3. Listagem de Tools: tools/list
            if rpc_method == "tools/list":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "tools": format_mcp_tools_list(),
                    },
                }
                return Response.new(json.dumps(response_data, ensure_ascii=False), status=200, headers=headers)

            # 3.4. Invocação de Tools: tools/call
            if rpc_method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                if tool_name == "discover":
                    tool_output = execute_discover().model_dump()
                elif tool_name == "hello":
                    validated_input = HelloInput(**args)
                    tool_output = execute_hello(validated_input).model_dump()
                elif tool_name == "calc":
                    validated_input = CalcInput(**args)
                    tool_output = execute_calc(validated_input).model_dump()
                else:
                    return Response.new(
                        json.dumps({
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {"code": -32601, "message": f"Ferramenta '{tool_name}' não encontrada."},
                        }),
                        status=404,
                        headers=headers,
                    )

                response_data = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_output, ensure_ascii=False),
                            }
                        ],
                        "structuredContent": tool_output,
                        "isError": False,
                    },
                }
                return Response.new(json.dumps(response_data, ensure_ascii=False), status=200, headers=headers)

            # Método desconhecido
            return Response.new(
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32601, "message": f"Método '{rpc_method}' não suportado."},
                }),
                status=400,
                headers=headers,
            )

        except Exception as exc:
            return Response.new(
                json.dumps({
                    "jsonrpc": "2.0",
                    "id": rpc_id if "rpc_id" in locals() else None,
                    "error": {"code": -32602, "message": f"Erro de validação ou execução: {str(exc)}"},
                }),
                status=400,
                headers=headers,
            )

    return Response.new("Método HTTP não suportado", status=405, headers=headers)
