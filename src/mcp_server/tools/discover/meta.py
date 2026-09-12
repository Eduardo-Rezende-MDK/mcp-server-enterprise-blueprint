"""Metadata and LLM heuristics for the 'discover' MCP tool."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "discover",
    "description": "Lista todas as ferramentas (tools) disponíveis no servidor MCP com seus respectivos schemas de entrada, saída e exemplos de uso.",
    "documentation": DocumentationDefinition(
        summary="Permite ao agente de IA inspecionar dinamicamente o catálogo de tools, seus contratos de dados e instruções de chamada.",
        usageGuidelines="Invoque esta tool no início de uma sessão ou quando precisar descobrir quais ferramentas estão ativas e quais parâmetros exatos elas esperam.",
        examples=[
            ExampleDefinition(
                scenario="Agente consulta o catálogo de tools disponíveis no servidor",
                input={},
                expectedOutput={
                    "total": 3,
                    "tools": [
                        {"name": "discover", "description": "Lista todas as ferramentas..."},
                        {"name": "hello", "description": "Retorna uma mensagem de saudação..."},
                        {"name": "calc", "description": "Calcula o resultado de uma operação matemática..."},
                    ],
                },
            )
        ],
    ),
}
