"""Template de Schemas Pydantic para novas MCP Tools.

Copie este arquivo ao criar uma nova tool ou utilize 'python -m mcp_server.scaffold <nome_da_tool>' ou via skill control-server-entreprise.
"""

from ...schemas.base import BaseModel, Field


class TemplateInput(BaseModel):
    """Parâmetros de entrada esperados pela ferramenta."""

    parametro_exemplo: str = Field(
        ...,
        min_length=1,
        description="Descrição clara do parâmetro para orientação semântica do LLM",
        examples=["exemplo_1", "exemplo_2"],
    )


class TemplateOutput(BaseModel):
    """Contrato de dados do resultado determinístico retornado pela ferramenta."""

    resultado: str = Field(..., description="Resultado formatado da execução")
    status: str = Field(default="sucesso", description="Status da execução da ferramenta")
