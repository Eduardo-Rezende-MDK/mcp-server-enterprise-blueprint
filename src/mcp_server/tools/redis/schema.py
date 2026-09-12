"""Schemas for the 'redis' MCP tool."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from ...schemas.base import BaseModel, Field


class RedisAction(str, Enum):
    """Operações determinísticas suportadas no Redis."""

    PING = "ping"
    GET = "get"
    SET = "set"
    DEL = "del"
    EXISTS = "exists"
    EXPIRE = "expire"
    TTL = "ttl"
    KEYS = "keys"
    HGET = "hget"
    HSET = "hset"
    HGETALL = "hgetall"
    HDEL = "hdel"
    SADD = "sadd"
    SMEMBERS = "smembers"


class RedisInput(BaseModel):
    """Parâmetros de entrada para operações em banco Redis."""

    action: RedisAction = Field(
        default=RedisAction.PING,
        description="Ação a ser executada no Redis: 'ping', 'get', 'set', 'del', 'exists', 'expire', 'ttl', 'keys', 'hget', 'hset', 'hgetall', 'hdel', 'sadd', 'smembers'",
        examples=["ping", "get", "set", "hgetall"],
    )
    key: Optional[str] = Field(
        default=None,
        description="Chave do Redis para operações de string, hash ou set (ex: 'auth:token:mcp_live_123', 'auth:user:eduardo@empresa.com')",
        examples=["auth:token:mcp_live_123", "config:settings", "user:1001"],
    )
    value: Optional[Any] = Field(
        default=None,
        description="Valor a ser armazenado na chave (para ação 'set'). Pode ser string, número ou dicionário/JSON.",
        examples=["ativo", {"name": "Eduardo", "role": "admin"}, 42],
    )
    ex: Optional[int] = Field(
        default=None,
        description="Tempo de expiração (TTL) em segundos para a chave (usado em 'set' ou 'expire')",
        examples=[60, 3600, 86400],
    )
    field: Optional[str] = Field(
        default=None,
        description="Nome do campo em operações de Hash ('hget', 'hdel')",
        examples=["name", "email", "status"],
    )
    fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dicionário de campos e valores para operações de Hash ('hset')",
        examples=[{"name": "Eduardo Rezende", "email": "eduardo@empresa.com", "status": "active"}],
    )
    pattern: Optional[str] = Field(
        default="*",
        description="Padrão de busca de chaves para ação 'keys' (ex: 'auth:*', 'cache:*')",
        examples=["auth:*", "user:*", "*"],
    )
    member: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Membro ou lista de membros para operações de Set ('sadd')",
        examples=["eduardo@empresa.com", ["user1", "user2"]],
    )


class ConnectionInfo(BaseModel):
    """Informações sobre a conexão ativa com o Redis."""

    backend: str = Field(..., description="Tipo de backend: 'upstash_rest', 'redis_tcp' ou 'in_memory_mock'")
    status: str = Field(..., description="Status da conexão: 'connected' ou 'error'")
    latency_ms: Optional[float] = Field(default=None, description="Latência medida do comando PING em milissegundos")
    endpoint: Optional[str] = Field(default=None, description="Endpoint ou identificador do servidor conectado")


class RedisOutput(BaseModel):
    """Resultado estruturado de uma operação Redis."""

    success: bool = Field(..., description="Indica se o comando foi executado com sucesso")
    action: str = Field(..., description="Ação executada")
    result: Optional[Any] = Field(default=None, description="Resultado bruto do comando (valor, booleano, contagem ou lista)")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Dados estruturados retornados (ex: dicionário de hash em hgetall)")
    keys: Optional[List[str]] = Field(default=None, description="Lista de chaves retornadas pela ação 'keys'")
    connection: Optional[ConnectionInfo] = Field(default=None, description="Detalhes e telemetria da conexão Redis")
    error: Optional[str] = Field(default=None, description="Mensagem de erro detalhada em caso de falha")
