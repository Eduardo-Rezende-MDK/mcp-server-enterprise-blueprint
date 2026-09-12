"""Test suite for live Cloudflare Worker deployment of MCP Enterprise Server."""

import json
import urllib.request

WORKER_URL = "https://mcp-server-enterprise.danicardoso-3011.workers.dev"


def call_rpc(method: str, params: dict = None, request_id: int = 1) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        payload["params"] = params

    req = urllib.request.Request(
        WORKER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MCP-Enterprise-Client/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_get_health():
    print("\n--- 1. Testing GET / (Health & Metadata) ---")
    req = urllib.request.Request(
        WORKER_URL,
        headers={"User-Agent": "MCP-Enterprise-Client/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Status: {resp.status}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        assert data["status"] == "online"
        assert data["server"] == "mcp-server-enterprise"
        assert data["tools_count"] == 3


def test_rpc_initialize():
    print("\n--- 2. Testing RPC initialize ---")
    resp = call_rpc("initialize", request_id=1)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "mcp-server-enterprise"


def test_rpc_tools_list():
    print("\n--- 3. Testing RPC tools/list ---")
    resp = call_rpc("tools/list", request_id=2)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    tools = resp["result"]["tools"]
    assert len(tools) == 3
    names = [t["name"] for t in tools]
    assert "discover" in names
    assert "hello" in names
    assert "calc" in names


def test_rpc_call_hello():
    print("\n--- 4. Testing RPC tools/call: hello ---")
    resp = call_rpc("tools/call", params={"name": "hello", "arguments": {"name": "Eduardo Rezende"}}, request_id=3)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    assert resp["id"] == 3
    assert resp["result"]["isError"] is False
    assert "Eduardo Rezende" in resp["result"]["structuredContent"]["message"]


def test_rpc_call_calc():
    print("\n--- 5. Testing RPC tools/call: calc ---")
    resp = call_rpc("tools/call", params={"name": "calc", "arguments": {"valor1": 150.0, "valor2": 25.0, "operacao": "/"}}, request_id=4)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    assert resp["id"] == 4
    assert resp["result"]["isError"] is False
    assert resp["result"]["structuredContent"]["resultado"] == 6.0
    assert resp["result"]["structuredContent"]["formula"] == "150 / 25 = 6"


def test_rpc_call_discover():
    print("\n--- 6. Testing RPC tools/call: discover ---")
    resp = call_rpc("tools/call", params={"name": "discover", "arguments": {}}, request_id=5)
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    assert resp["id"] == 5
    assert resp["result"]["isError"] is False
    assert resp["result"]["structuredContent"]["total"] == 3


if __name__ == "__main__":
    test_get_health()
    test_rpc_initialize()
    test_rpc_tools_list()
    test_rpc_call_hello()
    test_rpc_call_calc()
    test_rpc_call_discover()
    print("\n\n==========================================")
    print(" ALL 6 EDGE MCP CLOUDFLARE TESTS PASSED!")
    print("==========================================")
