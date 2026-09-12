"""Metadados e heurísticas semânticas para a MCP Tool 'sqlite'."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "sqlite",
    "description": "Executa operações determinísticas em banco de dados SQLite (CRUD e consultas SQL parametrizadas).",
    "documentation": DocumentationDefinition(
        summary="Permite criar tabelas, inserir registros, consultar com filtros, atualizar e excluir dados de forma determinística e segura em banco SQLite.",
        usageGuidelines="Invoque esta ferramenta quando o usuário solicitar persistência de dados, consultas SQL, relatórios em banco de dados ou operações CRUD em SQLite.",
        examples=[
            ExampleDefinition(
                scenario="Criar uma nova tabela de clientes",
                input={
                    "action": "query",
                    "query": "CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT)",
                    "db_name": ":memory:",
                },
                expectedOutput={
                    "success": True,
                    "message": "Query executada com sucesso.",
                    "rows_affected": 0,
                },
            ),
            ExampleDefinition(
                scenario="Inserir um novo registro na tabela clientes",
                input={
                    "action": "insert",
                    "table": "clientes",
                    "data": {"nome": "Eduardo Rezende", "email": "eduardo@empresa.com"},
                    "db_name": ":memory:",
                },
                expectedOutput={
                    "success": True,
                    "message": "Registro inserido com sucesso na tabela 'clientes' (ID: 1).",
                    "rows_affected": 1,
                    "last_row_id": 1,
                },
            ),
            ExampleDefinition(
                scenario="Consultar registros na tabela clientes",
                input={
                    "action": "select",
                    "table": "clientes",
                    "where": {"id": 1},
                    "limit": 10,
                    "db_name": ":memory:",
                },
                expectedOutput={
                    "success": True,
                    "message": "1 registros encontrados na tabela 'clientes'.",
                    "rows": [{"id": 1, "nome": "Eduardo Rezende", "email": "eduardo@empresa.com"}],
                },
            ),
        ],
    ),
}
