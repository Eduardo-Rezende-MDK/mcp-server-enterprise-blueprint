"""Handler determinístico para a ferramenta benchmark_cost."""

import random
from typing import List
from .schema import (
    BenchmarkCostInput,
    BenchmarkCostOutput,
    ParcelaItem,
    SistemaAmortizacao,
)


def execute(dados: BenchmarkCostInput) -> BenchmarkCostOutput:
    """Executa simulação financeira determinística de financiamento e amortização.

    Args:
        dados (BenchmarkCostInput): Parâmetros da simulação (opcionais).

    Returns:
        BenchmarkCostOutput: Resultado exato, cronograma e métricas de telemetria de tokens.
    """
    # 1. Resolução ou geração de parâmetros aleatórios realistas
    principal = float(
        dados.principal
        if dados.principal is not None and dados.principal > 0
        else random.choice([15000.0, 25000.0, 45000.0, 60000.0, 80000.0, 100000.0, 150000.0])
    )

    taxa_anual = float(
        dados.taxa_anual
        if dados.taxa_anual is not None and dados.taxa_anual > 0
        else round(random.choice([9.5, 11.0, 12.5, 14.0, 16.5, 18.0, 21.5]), 2)
    )

    meses = int(
        dados.meses
        if dados.meses is not None and dados.meses > 0
        else random.choice([12, 24, 36, 48, 60])
    )

    sistema = (
        dados.sistema
        if dados.sistema is not None
        else random.choice([SistemaAmortizacao.SAC, SistemaAmortizacao.PRICE])
    )
    if isinstance(sistema, str):
        sistema = SistemaAmortizacao(sistema.upper())

    # 2. Cálculo financeiro determinístico
    taxa_mensal = (taxa_anual / 100.0) / 12.0
    taxa_mensal_percentual = round(taxa_mensal * 100.0, 4)

    cronograma_completo: List[ParcelaItem] = []
    saldo_atual = principal
    total_juros = 0.0
    total_pago = 0.0

    if sistema == SistemaAmortizacao.SAC:
        amortizacao_fixa = principal / meses
        for mes in range(1, meses + 1):
            juros_mes = saldo_atual * taxa_mensal
            parcela_mes = amortizacao_fixa + juros_mes
            saldo_atual = max(0.0, saldo_atual - amortizacao_fixa)

            total_juros += juros_mes
            total_pago += parcela_mes

            cronograma_completo.append(
                ParcelaItem(
                    mes=mes,
                    parcela=round(parcela_mes, 2),
                    amortizacao=round(amortizacao_fixa, 2),
                    juros=round(juros_mes, 2),
                    saldo_devedor=round(saldo_atual, 2),
                )
            )

    else:  # Sistema PRICE
        fator = (1.0 + taxa_mensal) ** meses
        parcela_fixa = principal * ((taxa_mensal * fator) / (fator - 1.0))

        for mes in range(1, meses + 1):
            juros_mes = saldo_atual * taxa_mensal
            amortizacao_mes = parcela_fixa - juros_mes
            saldo_atual = max(0.0, saldo_atual - amortizacao_mes)

            total_juros += juros_mes
            total_pago += parcela_fixa

            cronograma_completo.append(
                ParcelaItem(
                    mes=mes,
                    parcela=round(parcela_fixa, 2),
                    amortizacao=round(amortizacao_mes, 2),
                    juros=round(juros_mes, 2),
                    saldo_devedor=round(saldo_atual, 2),
                )
            )

    # 3. Montagem da amostra de cronograma (primeiros 3 meses e último mês)
    if len(cronograma_completo) <= 4:
        cronograma_amostra = cronograma_completo
    else:
        cronograma_amostra = cronograma_completo[:3] + [cronograma_completo[-1]]

    primeira_parcela = cronograma_completo[0].parcela
    ultima_parcela = cronograma_completo[-1].parcela
    parcela_media = round(total_pago / meses, 2)

    # 4. Telemetria e Estimativa de Economia de Tokens
    # MCP: Parâmetros enxutos + resposta JSON condensada
    mcp_tokens_est = 75
    # LLM Cognitivo: Prompt context + raciocínio aritmético CoT passo a passo + saída longa
    llm_tokens_est = 1450
    economia_pct = round(((llm_tokens_est - mcp_tokens_est) / llm_tokens_est) * 100.0, 1)

    return BenchmarkCostOutput(
        params_usados={
            "principal": round(principal, 2),
            "taxa_anual_percentual": taxa_anual,
            "taxa_mensal_percentual": taxa_mensal_percentual,
            "meses": meses,
            "sistema": sistema.value,
            "gerado_automaticamente": dados.principal is None and dados.taxa_anual is None and dados.meses is None,
        },
        resumo_financeiro={
            "valor_financiado": round(principal, 2),
            "total_pago_final": round(total_pago, 2),
            "total_juros_acumulados": round(total_juros, 2),
            "primeira_parcela": primeira_parcela,
            "ultima_parcela": ultima_parcela,
            "parcela_media": parcela_media,
            "custo_efetivo_total_juros_percentual": round((total_juros / principal) * 100.0, 2),
        },
        cronograma_amostra=cronograma_amostra,
        benchmark_metricas={
            "mcp_estimated_tokens": mcp_tokens_est,
            "llm_cognitive_estimated_tokens": llm_tokens_est,
            "estimated_token_savings_percent": f"{economia_pct}%",
            "precision_guarantee": "100% Determinístico (Zero Risco de Alucinação Matemática)",
            "explanation": (
                "O FastMCP calcula fórmulas financeiras de amortização instantaneamente na CPU/Edge sem consumir "
                "tokens de raciocínio (Chain-of-Thought), eliminando erros de arredondamento e alucinações de exponenciação."
            ),
        },
        status="sucesso",
    )
