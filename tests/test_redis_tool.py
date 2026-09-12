"""Unit tests for the 'redis' MCP tool and Connection Manager."""

import time
import pytest
from mcp_server.registry import dispatch_tool
from mcp_server.tools.redis.handler import RedisConnectionManager
from mcp_server.tools.redis.schema import RedisAction, RedisInput, RedisOutput


def test_redis_ping_connection():
    """Valida o comando PING e handshake de conexão."""
    res = dispatch_tool("redis", {"action": "ping"})
    assert res["success"] is True
    assert res["action"] == "ping"
    assert res["result"] == "PONG"
    assert "connection" in res
    assert res["connection"]["status"] == "connected"
    assert res["connection"]["latency_ms"] is not None
    assert res["connection"]["backend"] in ("in_memory_mock", "upstash_rest", "redis_tcp")


def test_redis_set_and_get():
    """Valida operações de SET e GET."""
    key = "test:user:123"
    val = {"name": "Eduardo", "role": "admin"}

    set_res = dispatch_tool("redis", {"action": "set", "key": key, "value": val})
    assert set_res["success"] is True
    assert set_res["result"] == "OK"

    get_res = dispatch_tool("redis", {"action": "get", "key": key})
    assert get_res["success"] is True
    assert get_res["result"] == val


def test_redis_exists_and_del():
    """Valida EXISTS e DEL."""
    key = "test:temp:key"
    dispatch_tool("redis", {"action": "set", "key": key, "value": "123"})

    exists_res = dispatch_tool("redis", {"action": "exists", "key": key})
    assert exists_res["success"] is True
    assert exists_res["result"] == 1

    del_res = dispatch_tool("redis", {"action": "del", "key": key})
    assert del_res["success"] is True
    assert del_res["result"] == 1

    exists_res_after = dispatch_tool("redis", {"action": "exists", "key": key})
    assert exists_res_after["result"] == 0


def test_redis_ttl_and_expire():
    """Valida comando EXPIRE e consulta de TTL."""
    key = "test:ttl:key"
    dispatch_tool("redis", {"action": "set", "key": key, "value": "secret", "ex": 30})

    ttl_res = dispatch_tool("redis", {"action": "ttl", "key": key})
    assert ttl_res["success"] is True
    assert ttl_res["result"] > 0
    assert ttl_res["result"] <= 30


def test_redis_hashes():
    """Valida operações de Hash (HSET, HGET, HGETALL, HDEL)."""
    hkey = "auth:user:test@empresa.com"
    fields = {"name": "Eduardo", "email": "test@empresa.com", "status": "active"}

    hset_res = dispatch_tool("redis", {"action": "hset", "key": hkey, "fields": fields})
    assert hset_res["success"] is True

    hget_res = dispatch_tool("redis", {"action": "hget", "key": hkey, "field": "name"})
    assert hget_res["success"] is True
    assert hget_res["result"] == "Eduardo"

    hgetall_res = dispatch_tool("redis", {"action": "hgetall", "key": hkey})
    assert hgetall_res["success"] is True
    assert hgetall_res["data"]["email"] == "test@empresa.com"
    assert hgetall_res["data"]["status"] == "active"

    hdel_res = dispatch_tool("redis", {"action": "hdel", "key": hkey, "field": "status"})
    assert hdel_res["success"] is True
    assert hdel_res["result"] == 1


def test_redis_sets():
    """Valida operações de Set (SADD, SMEMBERS)."""
    skey = "auth:users:index"
    dispatch_tool("redis", {"action": "del", "key": skey})

    sadd_res = dispatch_tool("redis", {"action": "sadd", "key": skey, "member": ["user1@a.com", "user2@b.com"]})
    assert sadd_res["success"] is True

    smembers_res = dispatch_tool("redis", {"action": "smembers", "key": skey})
    assert smembers_res["success"] is True
    assert "user1@a.com" in smembers_res["result"]
    assert "user2@b.com" in smembers_res["result"]


def test_redis_keys_pattern():
    """Valida busca por padrão de chaves (KEYS)."""
    dispatch_tool("redis", {"action": "set", "key": "app:config:theme", "value": "dark"})
    dispatch_tool("redis", {"action": "set", "key": "app:config:lang", "value": "pt-BR"})

    keys_res = dispatch_tool("redis", {"action": "keys", "pattern": "app:config:*"})
    assert keys_res["success"] is True
    assert "app:config:theme" in keys_res["keys"]
    assert "app:config:lang" in keys_res["keys"]


def test_redis_validation_errors():
    """Valida tratamento de erros determinísticos para inputs inválidos."""
    res_no_key = dispatch_tool("redis", {"action": "get"})
    assert res_no_key["success"] is False
    assert "obrigatória" in res_no_key["error"]
