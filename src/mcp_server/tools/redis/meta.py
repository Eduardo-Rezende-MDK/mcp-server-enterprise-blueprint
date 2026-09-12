"""Metadados e heurísticas semânticas para a MCP Tool 'redis'."""

from ...schemas.common import DocumentationDefinition, ExampleDefinition

METADATA = {
    "name": "redis",
    "description": "Executa operações determinísticas em Redis (chave-valor, hashes, sets, TTLs e verificação de conectividade PING).",
    "documentation": DocumentationDefinition(
        summary="Permite gerenciar chaves, valores, hashes e sets com expiração automática (TTL) e suporte nativo a Upstash REST API para Edge Serverless e Cloudflare Workers.",
        usageGuidelines="Invoque esta ferramenta quando o usuário solicitar persistência em Redis, cache de dados, controle de tokens e sessões, operações de hash ou teste de conexão (PING).",
        examples=[
            ExampleDefinition(
                scenario="Testar a conexão ativa com o servidor Redis",
                input={
                    "action": "ping",
                },
                expectedOutput={
                    "success": True,
                    "action": "ping",
                    "result": "PONG",
                    "connection": {
                        "backend": "in_memory_mock",
                        "status": "connected",
                        "latency_ms": 0.15,
                    },
                },
            ),
            ExampleDefinition(
                scenario="Armazenar uma chave de token com TTL de 1 hora",
                input={
                    "action": "set",
                    "key": "auth:token:mcp_live_abc123",
                    "value": {"email": "eduardo@empresa.com", "name": "Eduardo Rezende"},
                    "ex": 3600,
                },
                expectedOutput={
                    "success": True,
                    "action": "set",
                    "result": "OK",
                },
            ),
            ExampleDefinition(
                scenario="Obter os dados do usuário a partir de um Hash",
                input={
                    "action": "hgetall",
                    "key": "auth:user:eduardo@empresa.com",
                },
                expectedOutput={
                    "success": True,
                    "action": "hgetall",
                    "data": {
                        "name": "Eduardo Rezende",
                        "email": "eduardo@empresa.com",
                        "status": "active",
                    },
                },
            ),
        ],
    ),
}
