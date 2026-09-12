"""Serverless Entrypoint for Cloudflare Workers in Native Python.

Exposes the MCP Enterprise Server deterministically over HTTP, JSON-RPC 2.0 and Web Portal Auth with Redis Token Management.
"""

import json
import os
from datetime import datetime, timezone
from js import Headers, Response
from urllib.parse import urlparse

from mcp_server.registry import TOOL_DEFINITIONS, dispatch_tool
from mcp_server.security import (
    extract_client_ip,
    get_token_metadata,
    is_tool_allowed_for_role,
    rate_limiter,
    validate_bearer_token,
)
from mcp_server.ui.portal import (
    get_portal_html,
    handle_google_login,
    handle_google_login_async,
    handle_lead_login,
    handle_lead_login_async,
)



def create_cors_headers(content_type: str = "application/json; charset=utf-8") -> Headers:
    """Cria os cabeçalhos padrão para habilitar CORS universal."""
    headers = Headers.new()
    headers.set("Access-Control-Allow-Origin", "*")
    headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, x-mcp-version, Accept")
    headers.set("Content-Type", content_type)
    return headers


def format_mcp_tools_list(role: str = "admin"):
    """Formata o catálogo de ferramentas no padrão oficial do protocolo MCP filtrando por perfil/role."""
    tools = []
    for tool in TOOL_DEFINITIONS:
        if not is_tool_allowed_for_role(tool.name, role):
            continue
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
    # Sincroniza variáveis de ambiente e secrets do Cloudflare Worker para os.environ
    if env is not None:
        try:
            if hasattr(env, "items"):
                for k, v in env.items():
                    if isinstance(v, str):
                        os.environ[k] = v
            else:
                for k in dir(env):
                    if not k.startswith("_"):
                        val = getattr(env, k, None)
                        if isinstance(val, (str, int, float, bool)):
                            os.environ[k] = str(val)
        except Exception:
            pass

    method = request.method
    raw_url = str(request.url)
    parsed_url = urlparse(raw_url)
    pathname = parsed_url.path or "/"

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

    # 3. Rota GET: Negociação de Conteúdo (HTML Landing Page vs. JSON Info)
    if method == "GET":
        # Extrai cabeçalho Accept
        accept_header = ""
        if hasattr(request.headers, "get"):
            accept_header = request.headers.get("accept") or request.headers.get("Accept") or ""
        elif isinstance(request.headers, dict):
            accept_header = request.headers.get("accept") or request.headers.get("Accept") or ""

        # Se acessado via navegador na raiz com Accept text/html, serve o Portal Web
        if pathname == "/" and ("text/html" in accept_header or not accept_header):
            html_headers = create_cors_headers("text/html; charset=utf-8")
            return Response.new(get_portal_html(), status=200, headers=html_headers)

        # Caso contrário, retorna metadados JSON do servidor MCP
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
                "header": "Authorization: Bearer mcp_live_<token>",
            },
            "rate_limit": {
                "limit": 60,
                "remaining": remaining,
                "window": "1h",
            },
            "tools_count": len(TOOL_DEFINITIONS),
            "tools": tool_names,
            "endpoints": {
                "portal": "GET / (Navegador text/html)",
                "auth_login": "POST /api/auth/login",
                "auth_google": "POST /api/auth/google",
                "rpc": "POST / (JSON-RPC 2.0)",
                "sse": "GET /sse (Server-Sent Events)",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return Response.new(json.dumps(info_payload, indent=2, ensure_ascii=False), status=200, headers=headers)

    # 4. Rota POST: Auth REST Endpoints ou JSON-RPC 2.0
    if method == "POST":
        # Endpoints REST de Autenticação (não usam JSON-RPC)
        if pathname == "/api/auth/login":
            try:
                body_text = await request.text()
                body_json = json.loads(body_text) if body_text else {}
                login_res = await handle_lead_login_async(body_json)
                status_code = 200 if login_res.get("success") else 400
                return Response.new(json.dumps(login_res, ensure_ascii=False), status=status_code, headers=headers)
            except Exception as exc:
                err_payload = {"success": False, "error": f"Falha ao processar cadastro: {str(exc)}"}
                return Response.new(json.dumps(err_payload, ensure_ascii=False), status=400, headers=headers)

        if pathname == "/api/auth/google":
            try:
                body_text = await request.text()
                body_json = json.loads(body_text) if body_text else {}
                google_res = await handle_google_login_async(body_json)
                status_code = 200 if google_res.get("success") else 400
                return Response.new(json.dumps(google_res, ensure_ascii=False), status=status_code, headers=headers)
            except Exception as exc:
                err_payload = {"success": False, "error": f"Falha ao autenticar Google: {str(exc)}"}
                return Response.new(json.dumps(err_payload, ensure_ascii=False), status=400, headers=headers)


        try:
            body_text = await request.text()
            if not body_text:
                return Response.new(
                    json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Corpo da requisição vazio"}}),
                    status=400,
                    headers=headers,
                )

            body_json = json.loads(body_text)

            # 4.3. Processamento JSON-RPC 2.0 (MCP Protocol)
            rpc_request = body_json
            rpc_id = rpc_request.get("id")
            rpc_method = rpc_request.get("method")
            params = rpc_request.get("params", {})

            # Handshake: initialize
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

            # Notificação: notifications/initialized
            if rpc_method == "notifications/initialized":
                return Response.new("", status=204, headers=headers)

            # 🛡️ Verificação de Bearer Auth dinâmica no Redis para métodos protegidos (tools/list e tools/call)
            auth_header = None
            if hasattr(request.headers, "get"):
                auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
            elif isinstance(request.headers, dict):
                auth_header = request.headers.get("authorization") or request.headers.get("Authorization")

            user_meta = get_token_metadata(auth_header)
            if not user_meta:
                unauthorized_error = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32000,
                        "message": "Acesso não autorizado: Bearer Token ausente ou inválido no Redis.",
                    },
                }
                return Response.new(json.dumps(unauthorized_error, ensure_ascii=False), status=401, headers=headers)

            user_role = user_meta.get("role", "lead")

            # Listagem de Tools Protegida: tools/list (Filtrada por perfil/role)
            if rpc_method == "tools/list":
                response_data = {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "tools": format_mcp_tools_list(role=user_role),
                    },
                }
                return Response.new(json.dumps(response_data, ensure_ascii=False), status=200, headers=headers)

            # Invocação de Tools Protegida: tools/call (com validação estrita de RBAC)
            if rpc_method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})

                # 🛡️ Bloqueio Perimetral de RBAC
                if not is_tool_allowed_for_role(tool_name, user_role):
                    forbidden_error = {
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "error": {
                            "code": -32003,
                            "message": f"Acesso negado: a ferramenta '{tool_name}' é restrita a administradores (role='admin'). Seu perfil de acesso é '{user_role}'.",
                        },
                    }
                    return Response.new(json.dumps(forbidden_error, ensure_ascii=False), status=403, headers=headers)

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
