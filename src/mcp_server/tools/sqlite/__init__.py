"""Ponto de exportação padrão do pacote da ferramenta.

Todo pacote de tool deve expor:
- `execute`: Função de execução determinística.
- `SqliteInput`: Modelo Pydantic dos parâmetros de entrada.
- `SqliteOutput`: Modelo Pydantic do resultado de saída.
- `METADATA`: Dicionário com metadados semânticos e documentação para o LLM.
"""

from .handler import execute
from .meta import METADATA
from .schema import SqliteInput, SqliteOutput

__all__ = ["execute", "SqliteInput", "SqliteOutput", "METADATA"]
