"""Serverless Entrypoint for Cloudflare Workers in Native Python.

Exposes the MCP Enterprise Server deterministically over HTTP and JSON-RPC 2.0 with Bearer Authentication and Rate Limiting.
"""

import json
from datetime import datetime, timezone
from js import Headers, Response

from mcp_server.registry import TOOL_DEFINITIONS, dispatch_tool
from mcp_server.security import extract_client_ip, rate_limiter, validate_bearer_token


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
        doc_dict = tool.documentation.model_dump() if hasattr(tool.documentation, "model_dump") else tool.documentation
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "outputSchema": tool.outputSchema,
            "documentation": doc_dict,
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

    # 2. ⏱️ Proteção Perimetral — Rate Limiting (60 req/h por IP)
    client_ip = extract_client_ip(request.headers)
    allowed, remaining = rate_limiter.is_allowed(client_ip)
    if not allowed:
        rate_limit_error = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32029,
                "message": "Limite de requisições atingido: máximo de 60 chamadas por hora por IP.",
            },
        }
        return Response.new(json.dumps(rate_limit_error, ensure_ascii=False), status=429, headers=headers)

    # 3. Rota de Health Check / Info (GET)
    if method == "GET":
        tool_names = [t.name for t in TOOL_DEFINITIONS]
        info_payload = {
            "status": "online",
            "server": "mcp-server-enterprise",
            "version": "1.0.0",
            "runtime": "Cloudflare Workers Python (Pyodide Edge)",
            "protocolVersion": "2024-11-05",
            "auth": {
                "required": True,
                "type": "Bearer",
                "header": "Authorization: Bearer rezende",
            },
            "rate_limit": {
                "limit": 60,
                "remaining": remaining,
                "window": "1h",
            },
            "tools_count": len(TOOL_DEFINITIONS),
            "tools": tool_names,
            "endpoints": {
                "rpc": "POST / (JSON-RPC 2.0)",
                "sse": "GET /sse (Server-Sent Events)",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return Response.new(json.dumps(info_payload, indent=2, ensure_ascii=False), status=200, headers=headers)

    # 4. Rota de Processamento JSON-RPC 2.0 (POST)
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

            # 4.1. Handshake: initialize (Permitido para negociação de capacidades)
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

            # 4.2. Notificação: notifications/initialized
            if rpc_method == "notifications/initialized":
                return Response.new("", status=204, headers=headers)

            # 4.3. 🛡️ Verificação de Bearer Auth para métodos protegidos (tools/list e tools/call)
            auth_header = None
            if hasattr(request.headers, "get"):
                auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            elif isinstance(request.headers, dict):
                auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

            if not validate_bearer_token(auth_header):
                unauthorized_error = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32000,
                        "message": "Acesso não autorizado: Bearer Token ausente ou inválido.",
                    },
                }
                return Response.new(json.dumps(unauthorized_error, ensure_ascii=False), status=401, headers=headers)

            # 4.4. Listagem de Tools Protegida: tools/list
            if rpc_method == "tools/list":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "tools": format_mcp_tools_list(),
                    },
                }
                return Response.new(json.dumps(response_data, ensure_ascii=False), status=200, headers=headers)

            # 4.5. Invocação de Tools Protegida: tools/call (Despacho Dinâmico)
            if rpc_method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                try:
                    tool_output = dispatch_tool(tool_name, args)
                except KeyError:
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
