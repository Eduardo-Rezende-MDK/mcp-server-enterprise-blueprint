"""Metadata and LLM heuristics for the 'hello' MCP tool."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "hello",
    "description": "Retorna uma mensagem de saudação personalizada com o nome fornecido, acompanhada da data e hora atual do sistema.",
    "documentation": DocumentationDefinition(
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
}
