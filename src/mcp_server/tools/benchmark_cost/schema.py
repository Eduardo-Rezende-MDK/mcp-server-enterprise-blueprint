"""Schemas Pydantic para a ferramenta benchmark_cost."""

from enum import Enum
from typing import Optional, List, Dict, Any
from ...schemas.base import BaseModel, Field


class SistemaAmortizacao(str, Enum):
    """Sistemas de amortização suportados."""

    SAC = "SAC"
    PRICE = "PRICE"


class ParcelaItem(BaseModel):
    """Detalhamento mensal da parcela de amortização."""

    mes: int = Field(..., description="Número do mês da parcela")
    parcela: float = Field(..., description="Valor total da prestação (Amortização + Juros)")
    amortizacao: float = Field(..., description="Valor amortizado do saldo devedor")
    juros: float = Field(..., description="Valor dos juros cobrados no mês")
    saldo_devedor: float = Field(..., description="Saldo devedor restante após o pagamento")


class BenchmarkCostInput(BaseModel):
    """Parâmetros de entrada para o simulador de benchmark financeiro.
    
    Todos os parâmetros são opcionais. Se omitidos, valores realistas serão gerados aleatoriamente.
    """

    principal: Optional[float] = Field(
        default=None,
        description="Valor principal financiado em R$ (ex: 50000.0). Se omitido, é gerado aleatoriamente.",
        examples=[50000.0, 120000.0],
    )
    taxa_anual: Optional[float] = Field(
        default=None,
        description="Taxa de juros anual em % (ex: 14.5). Se omitido, é gerado aleatoriamente.",
        examples=[12.5, 14.5],
    )
    meses: Optional[int] = Field(
        default=None,
        description="Prazo total em meses (ex: 24, 36, 48, 60). Se omitido, é gerado aleatoriamente.",
        examples=[24, 36],
    )
    sistema: Optional[SistemaAmortizacao] = Field(
        default=None,
        description="Sistema de amortização: 'SAC' (parcelas decrescentes) ou 'PRICE' (parcelas fixas). Se omitido, é gerado aleatoriamente.",
        examples=["SAC", "PRICE"],
    )


class BenchmarkCostOutput(BaseModel):
    """Contrato de retorno determinístico do benchmark financeiro."""

    params_usados: Dict[str, Any] = Field(
        ...,
        description="Parâmetros reais aplicados na simulação (gerados ou fornecidos)",
    )
    resumo_financeiro: Dict[str, Any] = Field(
        ...,
        description="Resumo dos valores calculados: total pago, juros acumulados, parcelas inicial/final",
    )
    cronograma_amostra: List[ParcelaItem] = Field(
        ...,
        description="Amostra do cronograma mensal (primeiros meses e mês final)",
    )
    benchmark_metricas: Dict[str, Any] = Field(
        ...,
        description="Telemetria e comparativo estimado de tokens (LLM Cognitivo vs FastMCP Determinístico)",
    )
    status: str = Field(
        default="sucesso",
        description="Status da execução da ferramenta",
    )
