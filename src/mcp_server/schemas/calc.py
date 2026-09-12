"""Schemas for the 'calc' MCP tool."""

from enum import Enum
from .base import BaseModel, Field


class OperacaoEnum(str, Enum):
    """Allowed mathematical operations."""

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

    valor1: float = Field(..., description="Primeiro valor numérico da operação")
    valor2: float = Field(..., description="Segundo valor numérico da operação (não pode ser 0 em divisão)")
    operacao: OperacaoEnum = Field(..., description="Operador matemático a ser aplicado")


class CalcOutput(BaseModel):
    """Output contract for the 'calc' tool."""

    resultado: float = Field(..., description="Resultado numérico exato da operação")
    formula: str = Field(..., description="Expressão matemática formatada e resolvida")
