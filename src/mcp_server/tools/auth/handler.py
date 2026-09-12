"""Handler determinístico para a ferramenta 'auth' com persistência em Redis."""

import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict
from ..redis.handler import execute as execute_redis
from .schema import AuthAction, AuthInput, AuthOutput

TOKEN_PREFIX = "mcp_live_"


def generate_secure_token() -> str:
    """Gera um Bearer Token criptograficamente seguro com prefixo padrão."""
    return f"{TOKEN_PREFIX}{secrets.token_hex(16)}"


def _validate_email(email: str) -> bool:
    """Valida formato básico de endereço de e-mail."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def execute(params: Dict[str, Any] | AuthInput) -> Dict[str, Any]:
    """Executa operações determinísticas de ciclo de vida de autenticação e tokens."""
    if isinstance(params, dict):
        input_data = AuthInput(**params)
    else:
        input_data = params

    action = input_data.action

    # 1. GERAÇÃO DE TOKEN CRIPTOGRÁFICO
    if action == AuthAction.TOKEN_GENERATOR:
        token = generate_secure_token()
        return AuthOutput(
            success=True,
            action=action.value,
            message="Token criptográfico gerado com sucesso.",
            token=token,
        ).model_dump()

    # 2. SETUP E TESTE DO REDIS
    if action == AuthAction.SETUP:
        ping_res = execute_redis({"action": "ping"})
        if ping_res.get("success"):
            return AuthOutput(
                success=True,
                action=action.value,
                message="Infraestrutura de autenticação em Redis validada e operacional.",
            ).model_dump()
        return AuthOutput(
            success=False,
            action=action.value,
            message="Falha ao inicializar infraestrutura de autenticação no Redis.",
            error=ping_res.get("error", "Erro de conexão com Redis"),
        ).model_dump()

    # 3. CADASTRO DE USUÁRIO E PERSISTÊNCIA DE TOKEN (SET_TOKEN)
    if action == AuthAction.SET_TOKEN:
        name = (input_data.name or "").strip()
        email = (input_data.email or "").strip().lower()

        if not name:
            return AuthOutput(
                success=False,
                action=action.value,
                message="O campo 'name' (nome completo) é obrigatório.",
                error="Nome obrigatório",
            ).model_dump()

        if not email or not _validate_email(email):
            return AuthOutput(
                success=False,
                action=action.value,
                message="O campo 'email' é obrigatório e deve ter um formato válido.",
                error="E-mail inválido ou ausente",
            ).model_dump()

        # Token fornecido ou novo gerado automaticamente
        token = (input_data.token or "").strip() or generate_secure_token()
        provider = input_data.provider or "local"
        google_id = input_data.google_id or ""
        now = datetime.now(timezone.utc).isoformat()

        # Verifica se o usuário já existe para preservar data de criação
        existing_user = execute_redis({"action": "hgetall", "key": f"auth:user:{email}"})
        user_dict = existing_user.get("data") or {}
        created_at = user_dict.get("created_at") or now

        # Se já existia um token anterior para o e-mail, revoga a chave antiga
        old_token = user_dict.get("token")
        if old_token and old_token != token:
            execute_redis({"action": "del", "key": f"auth:token:{old_token}"})

        user_data = {
            "name": name,
            "email": email,
            "token": token,
            "provider": provider,
            "google_id": google_id,
            "status": "active",
            "created_at": created_at,
            "last_login_at": now,
        }

        # 1. Salva o Hash do Usuário no Redis
        execute_redis({
            "action": "hset",
            "key": f"auth:user:{email}",
            "fields": user_data,
        })

        # 2. Salva o índice de busca rápida O(1) por Token
        execute_redis({
            "action": "set",
            "key": f"auth:token:{token}",
            "value": user_data,
        })

        # 3. Registra no Set de Usuários
        execute_redis({
            "action": "sadd",
            "key": "auth:users:index",
            "member": email,
        })

        return AuthOutput(
            success=True,
            action=action.value,
            message=f"Usuário '{name}' ({email}) registrado e token ativado com sucesso.",
            token=token,
            user=user_data,
        ).model_dump()

    # 4. VALIDAÇÃO E CONSULTA DE TOKEN (GET_TOKEN)
    if action == AuthAction.GET_TOKEN:
        token = (input_data.token or "").strip()
        email = (input_data.email or "").strip().lower()

        # A) Consulta por Token
        if token:
            # Busca no Redis O(1)
            token_res = execute_redis({"action": "get", "key": f"auth:token:{token}"})
            user_data = token_res.get("result")

            if user_data and isinstance(user_data, dict) and user_data.get("status") == "active":
                return AuthOutput(
                    success=True,
                    action=action.value,
                    message="Token autenticado e ativo no perímetro.",
                    token=token,
                    user=user_data,
                    is_valid=True,
                ).model_dump()

            return AuthOutput(
                success=True,
                action=action.value,
                message="Token não encontrado ou inativo.",
                token=token,
                user=None,
                is_valid=False,
            ).model_dump()

        # B) Consulta por E-mail
        if email:
            user_res = execute_redis({"action": "hgetall", "key": f"auth:user:{email}"})
            user_data = user_res.get("data") or {}

            if user_data and user_data.get("status") == "active":
                return AuthOutput(
                    success=True,
                    action=action.value,
                    message=f"Usuário '{email}' localizado com sucesso.",
                    token=user_data.get("token"),
                    user=user_data,
                    is_valid=True,
                ).model_dump()

            return AuthOutput(
                success=True,
                action=action.value,
                message=f"Nenhum cadastro ativo localizado para o e-mail '{email}'.",
                user=None,
                is_valid=False,
            ).model_dump()

        return AuthOutput(
            success=False,
            action=action.value,
            message="Informe 'token' para validação de acesso ou 'email' para consulta cadastral.",
            error="Parâmetros insuficientes",
        ).model_dump()

    return AuthOutput(
        success=False,
        action=action.value,
        message=f"Ação não reconhecida: {action}",
        error="Ação inválida",
    ).model_dump()
