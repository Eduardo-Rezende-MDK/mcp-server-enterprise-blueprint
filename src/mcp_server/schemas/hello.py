"""Schemas for the 'hello' MCP tool."""

from .base import BaseModel, Field


class HelloInput(BaseModel):
    """Input parameters for the 'hello' tool."""

    name: str = Field(
        ...,
        min_length=1,
        description="Nome da pessoa ou sistema a ser saudado",
    )


class HelloOutput(BaseModel):
    """Output contract for the 'hello' tool."""

    message: str = Field(..., description="Mensagem de saudação personalizada")
    timestamp: str = Field(..., description="Data e hora da execução no formato ISO 8601 (UTC)")
