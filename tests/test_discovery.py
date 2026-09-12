"""Unit tests for tool auto-discovery, dynamic registry, and scaffolding in MCP Enterprise Server."""

import shutil
from pathlib import Path
import pytest
from mcp_server.registry import build_tool_definitions, dispatch_tool, get_catalog
from mcp_server.tools import discover_tools
from mcp_server.scaffold import create_tool


class TestToolAutoDiscovery:
    """Testes para o mecanismo de auto-discovery de ferramentas."""

    def test_discover_tools_encontra_todas_as_tools_nativas(self):
        tools = discover_tools(force_reload=True)
        assert "hello" in tools
        assert "calc" in tools
        assert "discover" in tools
        assert len(tools) >= 3

    def test_discover_tools_ignora_templates_e_pastas_privadas(self):
        tools = discover_tools(force_reload=True)
        assert "_template" not in tools
        assert "__pycache__" not in tools

    def test_cada_tool_possui_contrato_completo(self):
        tools = discover_tools(force_reload=True)
        for name, pkg in tools.items():
            assert pkg.name == name
            assert pkg.description
            assert pkg.input_model is not None
            assert pkg.output_model is not None
            assert callable(pkg.execute)
            assert isinstance(pkg.metadata, dict)


class TestDynamicRegistry:
    """Testes para a geração dinâmica do catálogo e schemas Pydantic."""

    def test_build_tool_definitions_gera_json_schemas_validos(self):
        definitions = build_tool_definitions()
        names = [d.name for d in definitions]
        assert "hello" in names
        assert "calc" in names
        assert "discover" in names

        for tool_def in definitions:
            assert isinstance(tool_def.inputSchema, dict)
            assert "type" in tool_def.inputSchema
            assert isinstance(tool_def.outputSchema, dict)
            assert "type" in tool_def.outputSchema
            assert tool_def.documentation.summary
            assert tool_def.documentation.usageGuidelines

    def test_get_catalog_retorna_discover_output_integro(self):
        catalog = get_catalog()
        assert catalog.total >= 3
        assert len(catalog.tools) == catalog.total

    def test_dispatch_tool_executa_com_sucesso(self):
        # Teste hello via dispatch
        hello_res = dispatch_tool("hello", {"name": "Rezende"})
        assert "Rezende!" in hello_res["message"]
        assert "timestamp" in hello_res

        # Teste calc via dispatch
        calc_res = dispatch_tool("calc", {"valor1": 100, "valor2": 4, "operacao": "/"})
        assert calc_res["resultado"] == 25.0
        assert calc_res["formula"] == "100 / 4 = 25"

    def test_dispatch_tool_inexistente_lanca_key_error(self):
        with pytest.raises(KeyError, match="não encontrada"):
            dispatch_tool("ferramenta_fantasma", {})


class TestScaffoldingGenerator:
    """Testes para o gerador de scaffold create_tool.py."""

    def test_create_tool_scaffolding_e_auto_discovery(self):
        test_tool_name = "temp_test_scaffold"
        root_dir = Path(__file__).resolve().parent.parent
        target_dir = root_dir / "src" / "mcp_server" / "tools" / test_tool_name

        try:
            # 1. Cria tool temporária
            created_path = create_tool(test_tool_name, description="Tool de teste temporária")
            assert created_path.exists()
            assert (created_path / "schema.py").exists()
            assert (created_path / "handler.py").exists()
            assert (created_path / "meta.py").exists()
            assert (created_path / "__init__.py").exists()

            # 2. Força reload do discovery e valida reconhecimento
            tools = discover_tools(force_reload=True)
            assert test_tool_name in tools

            # 3. Executa via dispatch
            res = dispatch_tool(test_tool_name, {"parametro_exemplo": "teste_valor"})
            assert "teste_valor" in res["resultado"]

        finally:
            # Limpeza do ambiente de teste
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            # Restaura discovery limpo
            discover_tools(force_reload=True)
