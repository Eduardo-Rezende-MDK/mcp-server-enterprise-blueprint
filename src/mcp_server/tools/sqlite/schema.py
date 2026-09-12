"""Schemas for the 'sqlite' MCP tool."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from ...schemas.base import BaseModel, Field


class SqliteAction(str, Enum):
    """Operações CRUD suportadas pelo SQLite."""

    QUERY = "query"
    INSERT = "insert"
    SELECT = "select"
    UPDATE = "update"
    DELETE = "delete"


class SqliteInput(BaseModel):
    """Parâmetros de entrada para operações em banco SQLite."""

    action: SqliteAction = Field(
        default=SqliteAction.QUERY,
        description="Ação CRUD a ser executada: 'query', 'insert', 'select', 'update' ou 'delete'",
        examples=["query", "insert", "select"],
    )
    query: Optional[str] = Field(
        default=None,
        description="Instrução SQL a ser executada diretamente (ex: CREATE TABLE, SELECT, INSERT). Obrigatório se action='query'",
        examples=["CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)", "SELECT * FROM users"],
    )
    table: Optional[str] = Field(
        default=None,
        description="Nome da tabela alvo (usado em ações CRUD: insert, select, update, delete)",
        examples=["users", "pedidos", "produtos"],
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dicionário com colunas e valores a inserir ou atualizar (usado em insert e update)",
        examples=[{"name": "Eduardo", "email": "eduardo@empresa.com"}],
    )
    where: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="Filtro de busca ou condição WHERE (dicionário de igualdade ou string de condição)",
        examples=[{"id": 1}, "id = 1 AND status = 'ativo'"],
    )
    params: Optional[Union[List[Any], Dict[str, Any]]] = Field(
        default=None,
        description="Parâmetros posicionais ou nomeados para queries SQL parametrizadas",
        examples=[[1], {"status": "ativo"}],
    )
    limit: Optional[int] = Field(
        default=100,
        description="Limite máximo de registros retornados (usado em select)",
        examples=[10, 50, 100],
    )
    db_name: Optional[str] = Field(
        default=":memory:",
        description="Nome ou caminho do banco SQLite (padrão ':memory:' em memória, ou 'app.db')",
        examples=[":memory:", "app.db"],
    )


class SqliteOutput(BaseModel):
    """Resultado determinístico da operação SQLite."""

    success: bool = Field(..., description="Indica se a operação foi executada com sucesso")
    message: str = Field(..., description="Mensagem descritiva do resultado da operação")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de registros retornados (em formato dicionário)")
    rows_affected: int = Field(default=0, description="Quantidade de linhas inseridas, alteradas ou removidas")
    last_row_id: Optional[int] = Field(default=None, description="ID do último registro inserido com AUTOINCREMENT")
    columns: List[str] = Field(default_factory=list, description="Lista de nomes das colunas da consulta")
