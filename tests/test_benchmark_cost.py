"""Testes unitários e de integração para a ferramenta benchmark_cost."""

import pytest
from src.mcp_server.tools.benchmark_cost.schema import (
    BenchmarkCostInput,
    BenchmarkCostOutput,
    SistemaAmortizacao,
)
from src.mcp_server.tools.benchmark_cost.handler import execute
from src.mcp_server.registry import get_catalog, dispatch_tool


def test_benchmark_cost_sac_manual():
    """Valida o cálculo exato e determinístico para o sistema SAC."""
    dados = BenchmarkCostInput(
        principal=60000.0,
        taxa_anual=12.0,
        meses=12,
        sistema=SistemaAmortizacao.SAC,
    )
    resultado = execute(dados)

    assert isinstance(resultado, BenchmarkCostOutput)
    assert resultado.status == "sucesso"
    assert resultado.params_usados["principal"] == 60000.0
    assert resultado.params_usados["taxa_anual_percentual"] == 12.0
    assert resultado.params_usados["taxa_mensal_percentual"] == 1.0
    assert resultado.params_usados["meses"] == 12
    assert resultado.params_usados["sistema"] == "SAC"
    assert resultado.params_usados["gerado_automaticamente"] is False

    resumo = resultado.resumo_financeiro
    assert resumo["valor_financiado"] == 60000.0
    assert resumo["primeira_parcela"] == 5600.0
    assert resumo["ultima_parcela"] == 5050.0
    assert resumo["total_juros_acumulados"] == 3900.0
    assert resumo["total_pago_final"] == 63900.0

    amostra = resultado.cronograma_amostra
    assert len(amostra) == 4  # meses 1, 2, 3 e mês 12
    assert amostra[0].mes == 1
    assert amostra[0].parcela == 5600.0
    assert amostra[0].amortizacao == 5000.0
    assert amostra[0].juros == 600.0
    assert amostra[0].saldo_devedor == 55000.0

    assert amostra[-1].mes == 12
    assert amostra[-1].parcela == 5050.0
    assert amostra[-1].amortizacao == 5000.0
    assert amostra[-1].juros == 50.0
    assert amostra[-1].saldo_devedor == 0.0


def test_benchmark_cost_price_manual():
    """Valida o cálculo exato e determinístico para o sistema PRICE."""
    dados = BenchmarkCostInput(
        principal=10000.0,
        taxa_anual=12.0,
        meses=12,
        sistema=SistemaAmortizacao.PRICE,
    )
    resultado = execute(dados)

    assert resultado.status == "sucesso"
    assert resultado.params_usados["sistema"] == "PRICE"

    resumo = resultado.resumo_financeiro
    assert resumo["valor_financiado"] == 10000.0
    assert round(resumo["primeira_parcela"], 2) == 888.49
    assert round(resumo["ultima_parcela"], 2) == 888.49
    assert round(resumo["total_pago_final"], 2) == 10661.85
    assert round(resumo["total_juros_acumulados"], 2) == 661.85


def test_benchmark_cost_empty_args_random():
    """Valida a execução sem parâmetros gerando valores aleatórios consistentes."""
    dados = BenchmarkCostInput()
    resultado = execute(dados)

    assert resultado.status == "sucesso"
    assert resultado.params_usados["gerado_automaticamente"] is True
    assert resultado.params_usados["principal"] > 0
    assert resultado.params_usados["taxa_anual_percentual"] > 0
    assert resultado.params_usados["meses"] in [12, 24, 36, 48, 60]
    assert resultado.params_usados["sistema"] in ["SAC", "PRICE"]

    assert resultado.resumo_financeiro["total_pago_final"] > resultado.params_usados["principal"]
    assert resultado.resumo_financeiro["total_juros_acumulados"] > 0

    metricas = resultado.benchmark_metricas
    assert "mcp_estimated_tokens" in metricas
    assert "llm_cognitive_estimated_tokens" in metricas
    assert "estimated_token_savings_percent" in metricas
    assert "precision_guarantee" in metricas


def test_benchmark_cost_discovery_integration():
    """Valida se o discovery dinâmico registra e despacha a tool benchmark_cost."""
    catalogo = get_catalog()
    nomes = [tool.name for tool in catalogo.tools]
    assert "benchmark_cost" in nomes

    # Execução via dispatcher genérico
    resultado = dispatch_tool("benchmark_cost", {})
    assert resultado["status"] == "sucesso"
    assert "params_usados" in resultado
    assert "resumo_financeiro" in resultado
    assert "benchmark_metricas" in resultado
