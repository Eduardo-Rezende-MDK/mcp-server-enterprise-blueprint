"""Deterministic CLI caller for MCP Server Enterprise tools on Cloudflare Workers."""

import ast
import json
import sys
import time
import urllib.error
import urllib.request

WORKER_URL = "https://mcp-server-enterprise.mardukasoft.online"


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


def call_tool(tool_name: str, arguments: dict = None) -> tuple[dict, float]:
    """Executa uma ferramenta MCP de modo 100% deterministico via JSON-RPC 2.0."""
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

    req = urllib.request.Request(
        WORKER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MCP-Enterprise-CLI/1.0",
        },
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
        print("Uso: python scripts/call_tool.py <tool_name> [args_json]")
        print("Exemplos:")
        print("  python scripts/call_tool.py discover")
        print('  python scripts/call_tool.py hello \'{"name": "Eduardo"}\'')
        print('  python scripts/call_tool.py calc \'{"valor1": 150, "valor2": 25, "operacao": "/"}\'')
        sys.exit(1)

    tool_name = sys.argv[1]
    raw_args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "{}"

    try:
        arguments = parse_args_string(raw_args)
    except Exception as err:
        print(f"[ERRO]: {err}")
        sys.exit(1)

    print("\n==================================================================")
    print(f" >> INVOCACAO DETERMINISTICA MCP: tool='{tool_name}'")
    print("==================================================================")
    print(f"Parametros: {json.dumps(arguments, ensure_ascii=False)}")

    try:
        response, elapsed_ms = call_tool(tool_name, arguments)
        print(f"Latencia  : {elapsed_ms:.1f}ms")
        print("\n--- [Resultado Estruturado da Ferramenta] ---")
        if "result" in response and "structuredContent" in response["result"]:
            print(json.dumps(response["result"]["structuredContent"], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(response, indent=2, ensure_ascii=False))
        print("==================================================================\n")
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        print(f"\n[ERRO HTTP {err.code}]: {body}")
        sys.exit(1)
    except Exception as err:
        print(f"\n[ERRO DE CONEXAO]: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
