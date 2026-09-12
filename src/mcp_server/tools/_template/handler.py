"""Template de Handler Determinístico para novas MCP Tools.

Aqui reside exclusivamente a lógica pura de execução (sem probabilismos do LLM).
"""

from .schema import TemplateInput, TemplateOutput


def execute(dados: TemplateInput) -> TemplateOutput:
    """Executa deterministamente a lógica de negócio da ferramenta.

    Args:
        dados (TemplateInput): Dados de entrada já validados e tipados pelo Pydantic.

    Returns:
        TemplateOutput: Resultado estruturado conforme o contrato de saída.
    """
    param_limpo = dados.parametro_exemplo.strip()
    resultado_texto = f"Ferramenta processada com sucesso: {param_limpo}"

    return TemplateOutput(
        resultado=resultado_texto,
        status="sucesso",
    )
