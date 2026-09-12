"""Unit tests for deterministic MCP tools (discover, hello, calc)."""

from datetime import datetime
import pytest
from pydantic import ValidationError

from mcp_server.tools.calc.schema import CalcInput, OperacaoEnum
from mcp_server.tools.hello.schema import HelloInput
from mcp_server.tools.calc import execute as execute_calc
from mcp_server.tools.discover import execute as execute_discover
from mcp_server.tools.hello import execute as execute_hello


class TestDiscoverTool:
    """Testes unitários para a ferramenta 'discover'."""

    def test_discover_retorna_todas_as_ferramentas(self):
        catalogo = execute_discover()
        assert catalogo.total >= 3
        assert len(catalogo.tools) >= 3

        tool_names = [t.name for t in catalogo.tools]
        assert "discover" in tool_names
        assert "hello" in tool_names
        assert "calc" in tool_names

    def test_discover_contem_schemas_e_documentacao(self):
        catalogo = execute_discover()
        for tool in catalogo.tools:
            assert tool.name
            assert tool.description
            assert isinstance(tool.inputSchema, dict)
            assert isinstance(tool.outputSchema, dict)
            assert tool.documentation.summary
            assert tool.documentation.usageGuidelines
            assert len(tool.documentation.examples) > 0


class TestHelloTool:
    """Testes unitários para a ferramenta 'hello'."""

    def test_hello_retorna_saudacao_valida(self):
        dados = HelloInput(name="Eduardo")
        resposta = execute_hello(dados)
        assert "Olá, Eduardo!" in resposta.message
        assert "MCP Enterprise" in resposta.message

    def test_hello_retorna_timestamp_iso8601_valido(self):
        dados = HelloInput(name="Sistema")
        resposta = execute_hello(dados)
        ts = datetime.fromisoformat(resposta.timestamp)
        assert ts is not None

    def test_hello_rejeita_nome_vazio(self):
        with pytest.raises(ValidationError):
            HelloInput(name="")


class TestCalcTool:
    """Testes unitários para a ferramenta 'calc'."""

    @pytest.mark.parametrize(
        "v1, v2, op, esperado, formula_esperada",
        [
            (10.0, 5.0, OperacaoEnum.ADICAO, 15.0, "10 + 5 = 15"),
            (10.5, 3.2, OperacaoEnum.SOMA, 13.7, "10.5 + 3.2 = 13.7"),
            (20.0, 8.0, OperacaoEnum.SUBTRACAO, 12.0, "20 - 8 = 12"),
            (15.0, 5.0, OperacaoEnum.SUBTRACAO_NOME, 10.0, "15 - 5 = 10"),
            (6.0, 7.0, OperacaoEnum.MULTIPLICACAO, 42.0, "6 * 7 = 42"),
            (4.0, 2.5, OperacaoEnum.MULTIPLICACAO_NOME, 10.0, "4 * 2.5 = 10"),
            (150.0, 25.0, OperacaoEnum.DIVISAO, 6.0, "150 / 25 = 6"),
            (10.0, 4.0, OperacaoEnum.DIVISAO_NOME, 2.5, "10 / 4 = 2.5"),
        ],
    )
    def test_calc_operacoes_validas(self, v1, v2, op, esperado, formula_esperada):
        dados = CalcInput(valor1=v1, valor2=v2, operacao=op)
        resposta = execute_calc(dados)
        assert resposta.resultado == esperado
        assert resposta.formula == formula_esperada

    def test_calc_divisao_por_zero_lanca_erro(self):
        dados = CalcInput(valor1=100.0, valor2=0.0, operacao=OperacaoEnum.DIVISAO)
        with pytest.raises(ValueError, match="Divisão por zero não é permitida"):
            execute_calc(dados)

    def test_calc_operacao_invalida_lanca_validacao(self):
        with pytest.raises(ValidationError):
            CalcInput(valor1=10.0, valor2=5.0, operacao="invalida")  # type: ignore
