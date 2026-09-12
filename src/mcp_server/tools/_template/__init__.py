"""Ponto de exportação padrão do pacote da ferramenta.

Todo pacote de tool deve expor:
- `execute`: Função de execução determinística.
- `TemplateInput`: Modelo Pydantic dos parâmetros de entrada.
- `TemplateOutput`: Modelo Pydantic do resultado de saída.
- `METADATA`: Dicionário com metadados semânticos e documentação para o LLM.
"""

from .handler import execute
from .meta import METADATA
from .schema import TemplateInput, TemplateOutput

__all__ = ["execute", "TemplateInput", "TemplateOutput", "METADATA"]
