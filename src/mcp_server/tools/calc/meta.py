"""Metadata and LLM heuristics for the 'calc' MCP tool."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "calc",
    "description": "Calcula o resultado de uma operação matemática básica entre dois números (adição, subtração, multiplicação ou divisão).",
    "documentation": DocumentationDefinition(
        summary="Calculadora aritmética determinística para cálculos exatos e seguros.",
        usageGuidelines="O LLM DEVE delegar qualquer cálculo aritmético para esta ferramenta em vez de tentar calcular internamente, garantindo precisão numérica e eliminando alucinações matemáticas.",
        examples=[
            ExampleDefinition(
                scenario="Divisão de valores: 150 dividido por 25",
                input={"valor1": 150.0, "valor2": 25.0, "operacao": "/"},
                expectedOutput={"resultado": 6.0, "formula": "150 / 25 = 6"},
            ),
            ExampleDefinition(
                scenario="Soma com ponto flutuante: 10.5 + 3.2",
                input={"valor1": 10.5, "valor2": 3.2, "operacao": "+"},
                expectedOutput={"resultado": 13.7, "formula": "10.5 + 3.2 = 13.7"},
            ),
        ],
    ),
}
