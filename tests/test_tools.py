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
        assert "Eduardo!" in resposta.message
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


class TestSqliteTool:
    """Testes unitários para a ferramenta 'sqlite' (CRUD e queries)."""

    def test_sqlite_crud_completo(self):
        from mcp_server.tools.sqlite import execute as execute_sqlite
        from mcp_server.tools.sqlite.schema import SqliteAction, SqliteInput

        # 1. CREATE TABLE
        create_res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.QUERY,
                query="CREATE TABLE IF NOT EXISTS test_users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT)",
                db_name=":memory:",
            )
        )
        assert create_res.success is True

        # 2. INSERT
        insert_res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.INSERT,
                table="test_users",
                data={"name": "Alice Silva", "email": "alice@exemplo.com"},
                db_name=":memory:",
            )
        )
        assert insert_res.success is True
        assert insert_res.rows_affected == 1
        assert insert_res.last_row_id == 1

        # 3. SELECT
        select_res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.SELECT,
                table="test_users",
                where={"name": "Alice Silva"},
                db_name=":memory:",
            )
        )
        assert select_res.success is True
        assert len(select_res.rows) == 1
        assert select_res.rows[0]["email"] == "alice@exemplo.com"

        # 4. UPDATE
        update_res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.UPDATE,
                table="test_users",
                data={"email": "alice.nova@exemplo.com"},
                where={"id": 1},
                db_name=":memory:",
            )
        )
        assert update_res.success is True
        assert update_res.rows_affected == 1

        # 5. VERIFY UPDATE
        select_updated = execute_sqlite(
            SqliteInput(
                action=SqliteAction.SELECT,
                table="test_users",
                where={"id": 1},
                db_name=":memory:",
            )
        )
        assert select_updated.rows[0]["email"] == "alice.nova@exemplo.com"

        # 6. DELETE
        delete_res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.DELETE,
                table="test_users",
                where={"id": 1},
                db_name=":memory:",
            )
        )
        assert delete_res.success is True
        assert delete_res.rows_affected == 1

        # 7. VERIFY DELETE
        select_empty = execute_sqlite(
            SqliteInput(
                action=SqliteAction.SELECT,
                table="test_users",
                where={"id": 1},
                db_name=":memory:",
            )
        )
        assert len(select_empty.rows) == 0

    def test_sqlite_query_parametrizada(self):
        from mcp_server.tools.sqlite import execute as execute_sqlite
        from mcp_server.tools.sqlite.schema import SqliteAction, SqliteInput

        # Setup
        execute_sqlite(
            SqliteInput(
                action=SqliteAction.QUERY,
                query="CREATE TABLE IF NOT EXISTS test_products (id INTEGER PRIMARY KEY, title TEXT, price REAL)",
                db_name=":memory:",
            )
        )
        execute_sqlite(
            SqliteInput(
                action=SqliteAction.QUERY,
                query="INSERT INTO test_products (id, title, price) VALUES (?, ?, ?)",
                params=[1, "Notebook", 4500.50],
                db_name=":memory:",
            )
        )

        # Query com parametro
        res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.QUERY,
                query="SELECT * FROM test_products WHERE price > ?",
                params=[4000.0],
                db_name=":memory:",
            )
        )
        assert res.success is True
        assert len(res.rows) == 1
        assert res.rows[0]["title"] == "Notebook"
        assert res.columns == ["id", "title", "price"]

    def test_sqlite_rejeita_identificador_invalido(self):
        from mcp_server.tools.sqlite import execute as execute_sqlite
        from mcp_server.tools.sqlite.schema import SqliteAction, SqliteInput

        res = execute_sqlite(
            SqliteInput(
                action=SqliteAction.SELECT,
                table="users; DROP TABLE users;--",
                db_name=":memory:",
            )
        )
        assert res.success is False
        assert "Identificador SQL inválido" in res.message

