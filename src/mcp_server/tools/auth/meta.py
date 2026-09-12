"""Metadados e heurísticas semânticas para a MCP Tool 'auth'."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "auth",
    "description": "Gerencia o ciclo de vida de autenticação, cadastro de usuários (nome e e-mail), emissão de tokens criptográficos e validação perimetral no Redis.",
    "documentation": DocumentationDefinition(
        summary="Responsável pelo gerenciamento de identidade: emissão de tokens 'mcp_live_', cadastro de leads/usuários com persistência no Redis e validação perimetral O(1).",
        usageGuidelines="Invoque esta ferramenta quando precisar autenticar usuários, gerar ou validar Bearer Tokens, cadastrar novos leads (nome e e-mail) ou inicializar o namespace de autenticação.",
        examples=[
            ExampleDefinition(
                scenario="Cadastrar novo usuário e gerar Bearer Token",
                input={
                    "action": "set_token",
                    "name": "Eduardo Rezende",
                    "email": "eduardo@empresa.com",
                    "provider": "local",
                },
                expectedOutput={
                    "success": True,
                    "message": "Usuário 'Eduardo Rezende' (eduardo@empresa.com) registrado e token ativado com sucesso.",
                    "token": "mcp_live_e8471b045e758763118cfbf5ec94a02c",
                    "user": {
                        "name": "Eduardo Rezende",
                        "email": "eduardo@empresa.com",
                        "status": "active",
                    },
                },
            ),
            ExampleDefinition(
                scenario="Validar se um Bearer Token é autêntico e ativo",
                input={
                    "action": "get_token",
                    "token": "mcp_live_e8471b045e758763118cfbf5ec94a02c",
                },
                expectedOutput={
                    "success": True,
                    "is_valid": True,
                    "user": {
                        "name": "Eduardo Rezende",
                        "email": "eduardo@empresa.com",
                        "status": "active",
                    },
                },
            ),
            ExampleDefinition(
                scenario="Gerar um novo token criptográfico",
                input={
                    "action": "token_generator",
                },
                expectedOutput={
                    "success": True,
                    "token": "mcp_live_94f83b271d18204689cb32e0862a9381",
                },
            ),
        ],
    ),
}
