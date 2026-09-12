"""Deterministic CLI caller for MCP Server Enterprise tools on Cloudflare Workers."""

import ast
import json
import os
import sys
import time
import urllib.error
import urllib.request

WORKER_URL = os.environ.get("MCP_WORKER_URL", "https://mcp-server-enterprise.mardukasoft.online")


def _get_default_token() -> str:
    token = os.environ.get("MCP_BEARER_TOKEN") or os.environ.get("AUTH_TOKEN")
    if token:
        return token
    # Tenta ler do .env
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("AUTH_TOKEN="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return "MARDUKA"


DEFAULT_TOKEN = _get_default_token()


def parse_args_string(raw: str) -> dict:
    """Faz parsing seguro de argumentos JSON ou literais Python."""
    if not raw or raw.strip() in ("", "{}", '""'):
        return {}
    
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    try:
        return json.loads(raw.replace("'", '"'))
    except json.JSONDecodeError:
        pass

    try:
        val = ast.literal_eval(raw)
        if isinstance(val, dict):
            return val
    except Exception:
        pass

    raise ValueError(f"Formato invalido de argumentos JSON: {raw}")


def call_tool(tool_name: str, arguments: dict = None, token: str = DEFAULT_TOKEN) -> tuple[dict, float]:
    """Executa uma ferramenta MCP de modo 100% deterministico via JSON-RPC 2.0 com Bearer Auth."""
    if arguments is None:
        arguments = {}

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 100000,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MCP-Enterprise-CLI/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        WORKER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=10) as resp:
        duration_ms = (time.perf_counter() - t0) * 1000
        raw_body = resp.read().decode("utf-8")
        data = json.loads(raw_body)
        return data, duration_ms


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/call_tool.py <tool_name> [args_json] [--token <token>]")
        print("Exemplos:")
        print("  python scripts/call_tool.py discover")
        print('  python scripts/call_tool.py hello \'{"name": "Eduardo"}\'')
        print('  python scripts/call_tool.py calc \'{"valor1": 150, "valor2": 25, "operacao": "/"}\'')
        sys.exit(1)

    tool_name = sys.argv[1]
    raw_args = "{}"
    custom_token = DEFAULT_TOKEN

    args_list = sys.argv[2:]
    if "--token" in args_list:
        token_idx = args_list.index("--token")
        if token_idx + 1 < len(args_list):
            custom_token = args_list[token_idx + 1]
            args_list = args_list[:token_idx] + args_list[token_idx + 2:]

    if args_list:
        raw_args = " ".join(args_list)

    try:
        arguments = parse_args_string(raw_args)
    except Exception as err:
        print(f"[ERRO]: {err}")
        sys.exit(1)

    print("\n==================================================================")
    print(f" >> INVOCACAO DETERMINISTICA MCP: tool='{tool_name}'")
    print(f" >> Autenticacao: Bearer {custom_token[:3]}*** (Configurada)")
    print("==================================================================")
    print(f"Parametros: {json.dumps(arguments, ensure_ascii=False)}")

    try:
        response, elapsed_ms = call_tool(tool_name, arguments, token=custom_token)
        print(f"Latencia  : {elapsed_ms:.1f}ms")
        print("\n--- [Resultado Estruturado da Ferramenta] ---")
        if "result" in response and "structuredContent" in response["result"]:
            print(json.dumps(response["result"]["structuredContent"], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(response, indent=2, ensure_ascii=False))
        print("==================================================================\n")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        if err.code == 401:
            print(f"\n[ERRO HTTP 401 - Não Autorizado]: Bearer Token ausente ou inválido.")
        elif err.code == 429:
            print(f"\n[ERRO HTTP 429 - Rate Limit]: Limite de 60 requisições/hora excedido.")
        else:
            print(f"\n[ERRO HTTP {err.code}]: {body}")
        print(f"Detalhes: {body}")
        sys.exit(1)
    except Exception as err:
        print(f"\n[ERRO DE CONEXAO]: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
