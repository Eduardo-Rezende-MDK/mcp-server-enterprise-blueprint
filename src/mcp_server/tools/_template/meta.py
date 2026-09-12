"""Template de Metadados e Heurísticas Semânticas para o LLM.

Define a identidade semântica da ferramenta, diretrizes de invocação e exemplos práticos.
"""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "template_tool",
    "description": "Descrição semântica e objetiva do que a ferramenta realiza para o LLM decidir sua invocação.",
    "documentation": DocumentationDefinition(
        summary="Resumo funcional e objetivo da ferramenta.",
        usageGuidelines="Orientações e heurísticas estritas de quando o LLM DEVE ou NÃO DEVE invocar esta ferramenta.",
        examples=[
            ExampleDefinition(
                scenario="Descrição contextual de um cenário típico de chamada",
                input={"parametro_exemplo": "exemplo_1"},
                expectedOutput={
                    "resultado": "Ferramenta processada com sucesso: exemplo_1",
                    "status": "sucesso",
                },
            )
        ],
    ),
}
