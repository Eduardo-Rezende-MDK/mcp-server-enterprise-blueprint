"""Integration tests for FastMCP server tool invocations."""

import pytest
from mcp_server.server import calc, discover, hello, sqlite, mcp


class TestMcpServerIntegration:
    """Testes de integração das funções expostas no servidor FastMCP."""

    def test_mcp_instance_name(self):
        assert mcp.name == "mcp-server-enterprise"

    def test_server_discover_tool(self):
        res = discover()
        assert isinstance(res, dict)
        assert res["total"] >= 4
        assert len(res["tools"]) >= 4

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

    def test_server_sqlite_tool(self):
        # 1. Create table
        create_res = sqlite(
            action="query",
            query="CREATE TABLE IF NOT EXISTS demo_items (id INTEGER PRIMARY KEY, name TEXT)",
            db_name=":memory:",
        )
        assert create_res["success"] is True

        # 2. Insert
        insert_res = sqlite(
            action="insert",
            table="demo_items",
            data={"id": 10, "name": "Item A"},
            db_name=":memory:",
        )
        assert insert_res["success"] is True

        # 3. Select
        select_res = sqlite(
            action="select",
            table="demo_items",
            where={"id": 10},
            db_name=":memory:",
        )
        assert select_res["success"] is True
        assert len(select_res["rows"]) == 1
        assert select_res["rows"][0]["name"] == "Item A"
