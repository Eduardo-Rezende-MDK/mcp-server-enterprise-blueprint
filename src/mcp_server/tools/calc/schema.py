"""Schemas for the 'calc' MCP tool."""

from enum import Enum
from ...schemas.base import BaseModel, Field


class OperacaoEnum(str, Enum):
    """Supported mathematical operations."""

    ADICAO = "+"
    SUBTRACAO = "-"
    MULTIPLICACAO = "*"
    DIVISAO = "/"
    SOMA = "soma"
    SUBTRACAO_NOME = "subtracao"
    MULTIPLICACAO_NOME = "multiplicacao"
    DIVISAO_NOME = "divisao"


class CalcInput(BaseModel):
    """Input parameters for the 'calc' tool."""

    valor1: float = Field(
        ...,
        description="Primeiro valor numérico da operação",
        examples=[150.0, 10.5],
    )
    valor2: float = Field(
        ...,
        description="Segundo valor numérico da operação (não pode ser zero em divisões)",
        examples=[25.0, 3.2],
    )
    operacao: OperacaoEnum = Field(
        ...,
        description="Operador matemático a ser aplicado (+, -, *, / ou nomes por extenso)",
        examples=["/", "+"],
    )


class CalcOutput(BaseModel):
    """Output contract for the 'calc' tool."""

    resultado: float = Field(..., description="Resultado numérico exato da operação calculada")
    formula: str = Field(..., description="Expressão matemática resolvida formatada (ex: '150 / 25 = 6')")
