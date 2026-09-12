"""Registry and extended documentation catalog for MCP Enterprise Server."""

from typing import List
from .schemas.common import (
    DiscoverOutput,
    DocumentationDefinition,
    ExampleDefinition,
    ToolDefinition,
)

TOOL_DEFINITIONS: List[ToolDefinition] = [
    ToolDefinition(
        name="discover",
        description="Lista todas as ferramentas (tools) disponíveis no servidor MCP com seus respectivos schemas de entrada, saída e exemplos de uso.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "total": {"type": "integer", "description": "Quantidade total de ferramentas disponíveis"},
                "tools": {
                    "type": "array",
                    "description": "Lista de definições completas das ferramentas disponíveis",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Nome da ferramenta"},
                            "description": {"type": "string", "description": "Descrição da funcionalidade"},
                            "inputSchema": {"type": "object", "description": "Schema JSON dos parâmetros de entrada"},
                            "outputSchema": {"type": "object", "description": "Schema JSON do resultado retornado"},
                            "documentation": {"type": "object", "description": "Guia de uso e exemplos práticos"},
                        },
                        "required": ["name", "description", "inputSchema", "outputSchema", "documentation"],
                    },
                },
            },
            "required": ["tools", "total"],
        },
        documentation=DocumentationDefinition(
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
    ),
    ToolDefinition(
        name="hello",
        description="Retorna uma mensagem de saudação personalizada com o nome fornecido, acompanhada da data e hora atual do sistema.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nome da pessoa ou sistema a ser saudado",
                    "minLength": 1,
                }
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem de saudação formatada com nome, data e hora",
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Data e hora exatas da execução no formato ISO 8601 (UTC)",
                },
            },
            "required": ["message", "timestamp"],
        },
        documentation=DocumentationDefinition(
            summary="Gera saudação personalizada com carimbo de data e hora do sistema.",
            usageGuidelines="Invoque esta tool quando o usuário solicitar um teste de conectividade, uma saudação inicial ou quando for necessário obter o carimbo de data/hora atual do sistema para contextualização temporal.",
            examples=[
                ExampleDefinition(
                    scenario="Usuário pede para testar o servidor ou saudar 'Eduardo'",
                    input={"name": "Eduardo"},
                    expectedOutput={
                        "message": "Olá, Eduardo! Servidor MCP Enterprise operacional.",
                        "timestamp": "2026-09-11T22:10:00.000Z",
                    },
                )
            ],
        ),
    ),
    ToolDefinition(
        name="calc",
        description="Calcula o resultado de uma operação matemática básica entre dois números (adição, subtração, multiplicação ou divisão).",
        inputSchema={
            "type": "object",
            "properties": {
                "valor1": {"type": "number", "description": "Primeiro valor numérico da operação"},
                "valor2": {"type": "number", "description": "Segundo valor numérico da operação (não pode ser 0 em divisão)"},
                "operacao": {
                    "type": "string",
                    "description": "Operador matemático a ser aplicado",
                    "enum": ["+", "-", "*", "/", "soma", "subtracao", "multiplicacao", "divisao"],
                },
            },
            "required": ["valor1", "valor2", "operacao"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "resultado": {"type": "number", "description": "Resultado numérico exato da operação calculada"},
                "formula": {"type": "string", "description": "Expressão matemática resolvida (ex: '10 + 5 = 15')"},
            },
            "required": ["resultado", "formula"],
        },
        documentation=DocumentationDefinition(
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
    ),
]


def get_catalog() -> DiscoverOutput:
    """Retorna o catálogo completo de ferramentas ativas."""
    return DiscoverOutput(
        total=len(TOOL_DEFINITIONS),
        tools=TOOL_DEFINITIONS,
    )
