"""Handler determinístico para a ferramenta 'redis' e gerenciador de conexão."""

import fnmatch
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from .schema import ConnectionInfo, RedisAction, RedisInput, RedisOutput

# Carregamento automático de variáveis do arquivo .env se não estiverem no ambiente
def _load_env_file() -> None:
    candidate_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    for env_path in candidate_paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("\"'")
                        if k and k not in os.environ:
                            os.environ[k] = v
                break
            except Exception:
                pass

_load_env_file()

# Engine In-Memory thread-safe para fallback e testes determinísticos
_IN_MEMORY_STRINGS: Dict[str, Any] = {}
_IN_MEMORY_EXPIRATIONS: Dict[str, float] = {}
_IN_MEMORY_HASHES: Dict[str, Dict[str, Any]] = {}
_IN_MEMORY_SETS: Dict[str, Set[str]] = {}

# Cliente singleton do Redis TCP
_REDIS_CLIENT = None


class RedisConnectionManager:
    """Gerencia a conexão com o Redis suportando Upstash REST API, TCP e In-Memory Engine."""

    @staticmethod
    def get_config() -> Tuple[str, Optional[str], Optional[str]]:
        """Retorna o tipo de backend configurado e suas credenciais."""
        _load_env_file()
        upstash_url = os.environ.get("UPSTASH_REDIS_REST_URL", "").strip()
        upstash_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "").strip()
        redis_url = os.environ.get("REDIS_URL", "").strip()

        if upstash_url and upstash_token:
            return "upstash_rest", upstash_url, upstash_token
        if redis_url:
            return "redis_tcp", redis_url, None
        return "in_memory_mock", None, None

    @classmethod
    def get_tcp_client(cls, redis_url: str):
        """Retorna cliente redis-py instanciado de forma singleton e thread-safe."""
        global _REDIS_CLIENT
        if _REDIS_CLIENT is None:
            try:
                import redis
                _REDIS_CLIENT = redis.Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
            except Exception as exc:
                raise RuntimeError(f"Falha ao inicializar driver redis-py: {exc}")
        return _REDIS_CLIENT

    @classmethod
    def execute_upstash_command(cls, url: str, token: str, command: List[Any]) -> Any:
        """Executa um comando no Upstash Redis via HTTP REST API."""
        endpoint = url.rstrip("/")
        payload = json.dumps([str(arg) if not isinstance(arg, (int, float, bool)) else arg for arg in command]).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "error" in res_data:
                raise RuntimeError(f"Erro Upstash Redis: {res_data['error']}")
            return res_data.get("result")

    @classmethod
    def ping(cls) -> Tuple[bool, ConnectionInfo]:
        """Testa o status e latência da conexão ativa."""
        start_time = time.perf_counter()
        backend, url, token = cls.get_config()

        if backend == "upstash_rest":
            try:
                result = cls.execute_upstash_command(url, token, ["PING"])
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                masked_endpoint = url.split("://")[-1].split("@")[-1]
                return True, ConnectionInfo(
                    backend=backend,
                    status="connected" if result == "PONG" else "error",
                    latency_ms=latency,
                    endpoint=masked_endpoint,
                )
            except Exception as exc:
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                return False, ConnectionInfo(
                    backend=backend,
                    status="error",
                    latency_ms=latency,
                    endpoint=str(exc),
                )

        if backend == "redis_tcp" and url:
            try:
                client = cls.get_tcp_client(url)
                pong = client.ping()
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                # Mascarar credenciais na URL
                masked_endpoint = url.split("@")[-1] if "@" in url else url
                return True, ConnectionInfo(
                    backend="redis_tcp",
                    status="connected" if pong else "error",
                    latency_ms=latency,
                    endpoint=masked_endpoint,
                )
            except Exception as exc:
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                return False, ConnectionInfo(
                    backend="redis_tcp",
                    status="error",
                    latency_ms=latency,
                    endpoint=str(exc),
                )

        # In-Memory Mock (fallback)
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return True, ConnectionInfo(
            backend="in_memory_mock",
            status="connected",
            latency_ms=latency,
            endpoint="local://in-memory-engine",
        )


def _clean_expired_keys() -> None:
    """Remove chaves expiradas da memória local."""
    now = time.time()
    expired = [k for k, exp in _IN_MEMORY_EXPIRATIONS.items() if exp <= now]
    for k in expired:
        _IN_MEMORY_STRINGS.pop(k, None)
        _IN_MEMORY_HASHES.pop(k, None)
        _IN_MEMORY_SETS.pop(k, None)
        _IN_MEMORY_EXPIRATIONS.pop(k, None)


def execute_redis_tcp(input_data: RedisInput, redis_url: str) -> RedisOutput:
    """Executa operações Redis via TCP nativo usando redis-py."""
    action = input_data.action
    key = input_data.key or ""
    client = RedisConnectionManager.get_tcp_client(redis_url)

    if action == RedisAction.PING:
        _, conn = RedisConnectionManager.ping()
        return RedisOutput(success=True, action=action.value, result="PONG", connection=conn)

    if action == RedisAction.SET:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para SET")
        val = input_data.value
        val_str = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
        res = client.set(key, val_str, ex=input_data.ex)
        return RedisOutput(success=True, action=action.value, result="OK" if res else None)

    if action == RedisAction.GET:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para GET")
        val = client.get(key)
        if val is not None:
            try:
                val = json.loads(val)
            except Exception:
                pass
        return RedisOutput(success=True, action=action.value, result=val)

    if action == RedisAction.DEL:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para DEL")
        res = client.delete(key)
        return RedisOutput(success=True, action=action.value, result=res)

    if action == RedisAction.EXISTS:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para EXISTS")
        res = client.exists(key)
        return RedisOutput(success=True, action=action.value, result=res)

    if action == RedisAction.EXPIRE:
        if not key or input_data.ex is None:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'ex' são obrigatórios para EXPIRE")
        res = client.expire(key, input_data.ex)
        return RedisOutput(success=True, action=action.value, result=1 if res else 0)

    if action == RedisAction.TTL:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para TTL")
        ttl = client.ttl(key)
        return RedisOutput(success=True, action=action.value, result=ttl)

    if action == RedisAction.KEYS:
        pattern = input_data.pattern or "*"
        keys_list = client.keys(pattern)
        return RedisOutput(success=True, action=action.value, keys=keys_list, result=keys_list)

    if action == RedisAction.HSET:
        if not key or not input_data.fields:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'fields' são obrigatórios para HSET")
        fields_str = {
            k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
            for k, v in input_data.fields.items()
        }
        res = client.hset(key, mapping=fields_str)
        if input_data.ex:
            client.expire(key, input_data.ex)
        return RedisOutput(success=True, action=action.value, result=res)

    if action == RedisAction.HGET:
        if not key or not input_data.field:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'field' são obrigatórios para HGET")
        val = client.hget(key, input_data.field)
        if val is not None:
            try:
                val = json.loads(val)
            except Exception:
                pass
        return RedisOutput(success=True, action=action.value, result=val)

    if action == RedisAction.HGETALL:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para HGETALL")
        raw_dict = client.hgetall(key)
        parsed_dict = {}
        for k, v in raw_dict.items():
            try:
                parsed_dict[k] = json.loads(v)
            except Exception:
                parsed_dict[k] = v
        return RedisOutput(success=True, action=action.value, data=parsed_dict, result=parsed_dict)

    if action == RedisAction.HDEL:
        if not key or not input_data.field:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'field' são obrigatórios para HDEL")
        res = client.hdel(key, input_data.field)
        return RedisOutput(success=True, action=action.value, result=res)

    if action == RedisAction.SADD:
        if not key or not input_data.member:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'member' são obrigatórios para SADD")
        members = [input_data.member] if isinstance(input_data.member, str) else input_data.member
        res = client.sadd(key, *members)
        return RedisOutput(success=True, action=action.value, result=res)

    if action == RedisAction.SMEMBERS:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para SMEMBERS")
        members_list = list(client.smembers(key))
        return RedisOutput(success=True, action=action.value, result=members_list)

    return RedisOutput(success=False, action=action.value, error=f"Ação não implementada: {action}")


def execute_redis_in_memory(input_data: RedisInput) -> RedisOutput:
    """Executa operações Redis no motor in-memory local determinístico."""
    _clean_expired_keys()
    action = input_data.action
    key = input_data.key or ""

    if action == RedisAction.PING:
        _, conn = RedisConnectionManager.ping()
        return RedisOutput(success=True, action=action.value, result="PONG", connection=conn)

    if action == RedisAction.SET:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para SET")
        val = input_data.value
        _IN_MEMORY_STRINGS[key] = val
        if input_data.ex:
            _IN_MEMORY_EXPIRATIONS[key] = time.time() + input_data.ex
        else:
            _IN_MEMORY_EXPIRATIONS.pop(key, None)
        return RedisOutput(success=True, action=action.value, result="OK")

    if action == RedisAction.GET:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para GET")
        val = _IN_MEMORY_STRINGS.get(key)
        return RedisOutput(success=True, action=action.value, result=val)

    if action == RedisAction.DEL:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para DEL")
        deleted = 0
        if key in _IN_MEMORY_STRINGS:
            _IN_MEMORY_STRINGS.pop(key, None)
            deleted += 1
        if key in _IN_MEMORY_HASHES:
            _IN_MEMORY_HASHES.pop(key, None)
            deleted += 1
        if key in _IN_MEMORY_SETS:
            _IN_MEMORY_SETS.pop(key, None)
            deleted += 1
        _IN_MEMORY_EXPIRATIONS.pop(key, None)
        return RedisOutput(success=True, action=action.value, result=deleted)

    if action == RedisAction.EXISTS:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para EXISTS")
        exists = 1 if (key in _IN_MEMORY_STRINGS or key in _IN_MEMORY_HASHES or key in _IN_MEMORY_SETS) else 0
        return RedisOutput(success=True, action=action.value, result=exists)

    if action == RedisAction.EXPIRE:
        if not key or input_data.ex is None:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'ex' (segundos) são obrigatórios para EXPIRE")
        if key in _IN_MEMORY_STRINGS or key in _IN_MEMORY_HASHES or key in _IN_MEMORY_SETS:
            _IN_MEMORY_EXPIRATIONS[key] = time.time() + input_data.ex
            return RedisOutput(success=True, action=action.value, result=1)
        return RedisOutput(success=True, action=action.value, result=0)

    if action == RedisAction.TTL:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para TTL")
        if key not in _IN_MEMORY_STRINGS and key not in _IN_MEMORY_HASHES and key not in _IN_MEMORY_SETS:
            return RedisOutput(success=True, action=action.value, result=-2)
        if key not in _IN_MEMORY_EXPIRATIONS:
            return RedisOutput(success=True, action=action.value, result=-1)
        ttl_left = int(_IN_MEMORY_EXPIRATIONS[key] - time.time())
        return RedisOutput(success=True, action=action.value, result=max(0, ttl_left))

    if action == RedisAction.KEYS:
        pattern = input_data.pattern or "*"
        all_keys = set(_IN_MEMORY_STRINGS.keys()) | set(_IN_MEMORY_HASHES.keys()) | set(_IN_MEMORY_SETS.keys())
        matched = [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
        return RedisOutput(success=True, action=action.value, keys=matched, result=matched)

    if action == RedisAction.HSET:
        if not key or not input_data.fields:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'fields' são obrigatórios para HSET")
        if key not in _IN_MEMORY_HASHES:
            _IN_MEMORY_HASHES[key] = {}
        _IN_MEMORY_HASHES[key].update(input_data.fields)
        if input_data.ex:
            _IN_MEMORY_EXPIRATIONS[key] = time.time() + input_data.ex
        return RedisOutput(success=True, action=action.value, result=len(input_data.fields))

    if action == RedisAction.HGET:
        if not key or not input_data.field:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'field' são obrigatórios para HGET")
        hash_data = _IN_MEMORY_HASHES.get(key, {})
        val = hash_data.get(input_data.field)
        return RedisOutput(success=True, action=action.value, result=val)

    if action == RedisAction.HGETALL:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para HGETALL")
        hash_data = _IN_MEMORY_HASHES.get(key, {})
        return RedisOutput(success=True, action=action.value, data=hash_data, result=hash_data)

    if action == RedisAction.HDEL:
        if not key or not input_data.field:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'field' são obrigatórios para HDEL")
        hash_data = _IN_MEMORY_HASHES.get(key, {})
        if input_data.field in hash_data:
            hash_data.pop(input_data.field)
            return RedisOutput(success=True, action=action.value, result=1)
        return RedisOutput(success=True, action=action.value, result=0)

    if action == RedisAction.SADD:
        if not key or not input_data.member:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' e 'member' são obrigatórios para SADD")
        if key not in _IN_MEMORY_SETS:
            _IN_MEMORY_SETS[key] = set()
        members = [input_data.member] if isinstance(input_data.member, str) else input_data.member
        added = 0
        for m in members:
            if m not in _IN_MEMORY_SETS[key]:
                _IN_MEMORY_SETS[key].add(str(m))
                added += 1
        return RedisOutput(success=True, action=action.value, result=added)

    if action == RedisAction.SMEMBERS:
        if not key:
            return RedisOutput(success=False, action=action.value, error="Chave 'key' é obrigatória para SMEMBERS")
        members = list(_IN_MEMORY_SETS.get(key, set()))
        return RedisOutput(success=True, action=action.value, result=members)

    return RedisOutput(success=False, action=action.value, error=f"Ação não implementada: {action}")


def execute(params: Dict[str, Any] | RedisInput) -> Dict[str, Any]:
    """Executa a ferramenta 'redis' com validação estrita e suporte híbrido (TCP / REST / In-Memory)."""
    if isinstance(params, dict):
        input_data = RedisInput(**params)
    else:
        input_data = params

    backend, url, token = RedisConnectionManager.get_config()

    # 1. Se configurado via Redis TCP
    if backend == "redis_tcp" and url:
        try:
            res = execute_redis_tcp(input_data, url)
            return res.model_dump()
        except Exception as exc:
            return RedisOutput(success=False, action=input_data.action.value, error=f"Erro Redis TCP: {exc}").model_dump()

    # 2. Se configurado via Upstash REST
    if backend == "upstash_rest" and url and token:
        try:
            action = input_data.action

            if action == RedisAction.PING:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["PING"])
                _, conn = RedisConnectionManager.ping()
                return RedisOutput(success=True, action=action.value, result=res, connection=conn).model_dump()

            if action == RedisAction.GET and input_data.key:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["GET", input_data.key])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.SET and input_data.key:
                val = input_data.value
                val_str = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
                cmd = ["SET", input_data.key, val_str]
                if input_data.ex:
                    cmd.extend(["EX", input_data.ex])
                res = RedisConnectionManager.execute_upstash_command(url, token, cmd)
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.DEL and input_data.key:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["DEL", input_data.key])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.EXISTS and input_data.key:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["EXISTS", input_data.key])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.EXPIRE and input_data.key and input_data.ex is not None:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["EXPIRE", input_data.key, input_data.ex])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.TTL and input_data.key:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["TTL", input_data.key])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.KEYS:
                pattern = input_data.pattern or "*"
                res = RedisConnectionManager.execute_upstash_command(url, token, ["KEYS", pattern])
                return RedisOutput(success=True, action=action.value, keys=res or [], result=res).model_dump()

            if action == RedisAction.HSET and input_data.key and input_data.fields:
                cmd = ["HSET", input_data.key]
                for f_name, f_val in input_data.fields.items():
                    cmd.extend([f_name, json.dumps(f_val) if isinstance(f_val, (dict, list)) else str(f_val)])
                res = RedisConnectionManager.execute_upstash_command(url, token, cmd)
                if input_data.ex:
                    RedisConnectionManager.execute_upstash_command(url, token, ["EXPIRE", input_data.key, input_data.ex])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.HGET and input_data.key and input_data.field:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["HGET", input_data.key, input_data.field])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.HGETALL and input_data.key:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["HGETALL", input_data.key])
                data_dict = {}
                if isinstance(res, dict):
                    data_dict = res
                elif isinstance(res, list):
                    for i in range(0, len(res), 2):
                        if i + 1 < len(res):
                            data_dict[res[i]] = res[i + 1]
                return RedisOutput(success=True, action=action.value, data=data_dict, result=data_dict).model_dump()

            if action == RedisAction.HDEL and input_data.key and input_data.field:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["HDEL", input_data.key, input_data.field])
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.SADD and input_data.key and input_data.member:
                members = [input_data.member] if isinstance(input_data.member, str) else input_data.member
                cmd = ["SADD", input_data.key] + [str(m) for m in members]
                res = RedisConnectionManager.execute_upstash_command(url, token, cmd)
                return RedisOutput(success=True, action=action.value, result=res).model_dump()

            if action == RedisAction.SMEMBERS and input_data.key:
                res = RedisConnectionManager.execute_upstash_command(url, token, ["SMEMBERS", input_data.key])
                return RedisOutput(success=True, action=action.value, result=res or []).model_dump()

        except Exception as exc:
            return RedisOutput(success=False, action=input_data.action.value, error=f"Erro Upstash REST: {exc}").model_dump()

    # 3. Fallback / Execução In-Memory Engine
    result = execute_redis_in_memory(input_data)
    return result.model_dump()
