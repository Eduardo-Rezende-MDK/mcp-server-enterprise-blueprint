"""Metadados e Heurísticas Semânticas para o LLM da tool benchmark_cost."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "benchmark_cost",
    "description": (
        "Simulador determinístico de financiamento e amortização (SAC e PRICE). "
        "Calcula parcelas, amortização, juros acumulados e gera métricas de economia de tokens. "
        "Pode ser chamada sem nenhum parâmetro ({}) para auto-gerar um cenário aleatório realista."
    ),
    "documentation": DocumentationDefinition(
        summary="Simula empréstimos e financiamentos determinísticos e compara a eficiência de tokens.",
        usageGuidelines=(
            "Invoque esta ferramenta quando precisar simular financiamentos, empréstimos, tabelas SAC/PRICE, "
            "ou quando o usuário solicitar testes de benchmark de custo de tokens e comparação de eficiência."
        ),
        examples=[
            ExampleDefinition(
                scenario="Simulação automática sem parâmetros para benchmark de custo",
                input={},
                expectedOutput={
                    "status": "sucesso",
                    "params_usados": {
                        "principal": 50000.0,
                        "taxa_anual_percentual": 14.5,
                        "meses": 24,
                        "sistema": "SAC",
                        "gerado_automaticamente": True,
                    },
                    "resumo_financeiro": {
                        "valor_financiado": 50000.0,
                        "total_pago_final": 57552.08,
                        "total_juros_acumulados": 7552.08,
                        "primeira_parcela": 2687.5,
                        "ultima_parcela": 2108.68,
                    },
                },
            ),
            ExampleDefinition(
                scenario="Simulação com parâmetros customizados no sistema PRICE",
                input={
                    "principal": 80000.0,
                    "taxa_anual": 12.0,
                    "meses": 36,
                    "sistema": "PRICE",
                },
                expectedOutput={
                    "status": "sucesso",
                    "params_usados": {
                        "principal": 80000.0,
                        "taxa_anual_percentual": 12.0,
                        "meses": 36,
                        "sistema": "PRICE",
                        "gerado_automaticamente": False,
                    },
                },
            ),
        ],
    ),
}
