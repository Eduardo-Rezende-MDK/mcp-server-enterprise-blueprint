"""Handler determinístico para a ferramenta 'sqlite'."""

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple
from .schema import SqliteAction, SqliteInput, SqliteOutput

# Conexão em memória compartilhada global para sessões com ':memory:' persistentes em runtime
_MEMORY_DBS: Dict[str, sqlite3.Connection] = {}


def _get_connection(db_name: str) -> sqlite3.Connection:
    """Obtém ou cria uma conexão segura com o banco SQLite."""
    db_name = (db_name or ":memory:").strip()

    if db_name == ":memory:":
        if ":memory:" not in _MEMORY_DBS:
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _MEMORY_DBS[":memory:"] = conn
        return _MEMORY_DBS[":memory:"]

    # Validação de segurança para caminho de arquivo (prevenção de Path Traversal)
    clean_name = Path(db_name).name
    if not clean_name.endswith((".db", ".sqlite", ".sqlite3")):
        clean_name = f"{clean_name}.db"

    data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / clean_name

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _validate_identifier(name: str) -> str:
    """Valida identificadores SQL (tabelas e colunas) contra injeções."""
    if not name or not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        raise ValueError(f"Identificador SQL inválido: '{name}'")
    return name


def _build_where_clause(where: Any) -> Tuple[str, List[Any]]:
    """Gera cláusula WHERE parametrizada a partir de dicionário ou string."""
    if not where:
        return "", []

    if isinstance(where, dict):
        clauses = []
        values = []
        for col, val in where.items():
            valid_col = _validate_identifier(col)
            if val is None:
                clauses.append(f"{valid_col} IS NULL")
            else:
                clauses.append(f"{valid_col} = ?")
                values.append(val)
        return f" WHERE {' AND '.join(clauses)}", values

    if isinstance(where, str):
        # Validação simples para evitar caracteres perigosos
        return f" WHERE {where}", []

    return "", []


def execute(dados: SqliteInput) -> SqliteOutput:
    """Executa a operação CRUD ou consulta parametrizada no SQLite."""
    try:
        conn = _get_connection(dados.db_name)
        cursor = conn.cursor()
        action = dados.action

        # 1. AÇÃO: QUERY (SQL Direto / Parametrizado)
        if action == SqliteAction.QUERY:
            if not dados.query:
                return SqliteOutput(
                    success=False,
                    message="O campo 'query' é obrigatório para a ação 'query'.",
                )

            query_str = dados.query.strip()
            params = dados.params or ()

            # Executa com cursor
            if isinstance(params, (list, tuple, dict)):
                cursor.execute(query_str, params)
            else:
                cursor.execute(query_str)

            conn.commit()

            # Extração de linhas caso seja um SELECT/PRAGMA
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [dict(row) for row in cursor.fetchall()] if cursor.description else []
            affected = cursor.rowcount if cursor.rowcount != -1 else len(rows)

            return SqliteOutput(
                success=True,
                message=f"Query executada com sucesso. ({len(rows)} linhas retornadas, {affected} afetadas)",
                rows=rows,
                rows_affected=affected,
                last_row_id=cursor.lastrowid,
                columns=columns,
            )

        # 2. AÇÃO: INSERT
        if action == SqliteAction.INSERT:
            if not dados.table or not dados.data:
                return SqliteOutput(
                    success=False,
                    message="Os campos 'table' e 'data' são obrigatórios para a ação 'insert'.",
                )

            table = _validate_identifier(dados.table)
            columns = [_validate_identifier(k) for k in dados.data.keys()]
            values = list(dados.data.values())
            placeholders = ", ".join(["?"] * len(columns))

            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(sql, values)
            conn.commit()

            return SqliteOutput(
                success=True,
                message=f"Registro inserido com sucesso na tabela '{table}' (ID: {cursor.lastrowid}).",
                rows_affected=cursor.rowcount,
                last_row_id=cursor.lastrowid,
                columns=columns,
            )

        # 3. AÇÃO: SELECT
        if action == SqliteAction.SELECT:
            if not dados.table:
                return SqliteOutput(
                    success=False,
                    message="O campo 'table' é obrigatório para a ação 'select'.",
                )

            table = _validate_identifier(dados.table)
            where_sql, where_vals = _build_where_clause(dados.where)
            limit_val = max(1, min(dados.limit or 100, 1000))

            sql = f"SELECT * FROM {table}{where_sql} LIMIT {limit_val}"
            cursor.execute(sql, where_vals)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [dict(row) for row in cursor.fetchall()]

            return SqliteOutput(
                success=True,
                message=f"{len(rows)} registros encontrados na tabela '{table}'.",
                rows=rows,
                rows_affected=len(rows),
                columns=columns,
            )

        # 4. AÇÃO: UPDATE
        if action == SqliteAction.UPDATE:
            if not dados.table or not dados.data or not dados.where:
                return SqliteOutput(
                    success=False,
                    message="Os campos 'table', 'data' e 'where' são obrigatórios para a ação 'update'.",
                )

            table = _validate_identifier(dados.table)
            set_clauses = [f"{_validate_identifier(k)} = ?" for k in dados.data.keys()]
            set_vals = list(dados.data.values())

            where_sql, where_vals = _build_where_clause(dados.where)
            sql = f"UPDATE {table} SET {', '.join(set_clauses)}{where_sql}"

            cursor.execute(sql, set_vals + where_vals)
            conn.commit()

            return SqliteOutput(
                success=True,
                message=f"{cursor.rowcount} registro(s) atualizado(s) na tabela '{table}'.",
                rows_affected=cursor.rowcount,
            )

        # 5. AÇÃO: DELETE
        if action == SqliteAction.DELETE:
            if not dados.table or not dados.where:
                return SqliteOutput(
                    success=False,
                    message="Os campos 'table' e 'where' são obrigatórios para a ação 'delete'.",
                )

            table = _validate_identifier(dados.table)
            where_sql, where_vals = _build_where_clause(dados.where)

            sql = f"DELETE FROM {table}{where_sql}"
            cursor.execute(sql, where_vals)
            conn.commit()

            return SqliteOutput(
                success=True,
                message=f"{cursor.rowcount} registro(s) removido(s) da tabela '{table}'.",
                rows_affected=cursor.rowcount,
            )

        return SqliteOutput(success=False, message=f"Ação '{action}' não suportada.")

    except Exception as exc:
        return SqliteOutput(
            success=False,
            message=f"Erro na execução SQLite: {str(exc)}",
            rows_affected=0,
        )
