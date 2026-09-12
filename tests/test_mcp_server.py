"""Integration tests for FastMCP server tool invocations."""

import pytest
from mcp_server.server import calc, discover, hello, mcp


class TestMcpServerIntegration:
    """Testes de integração das funções expostas no servidor FastMCP."""

    def test_mcp_instance_name(self):
        assert mcp.name == "mcp-server-enterprise"

    def test_server_discover_tool(self):
        res = discover()
        assert isinstance(res, dict)
        assert res["total"] == 3
        assert len(res["tools"]) == 3

    def test_server_hello_tool(self):
        res = hello(name="Eduardo")
        assert isinstance(res, dict)
        assert "Eduardo!" in res["message"]
        assert "timestamp" in res

    def test_server_calc_tool(self):
        res = calc(valor1=150.0, valor2=25.0, operacao="/")
        assert isinstance(res, dict)
        assert res["resultado"] == 6.0
        assert res["formula"] == "150 / 25 = 6"
