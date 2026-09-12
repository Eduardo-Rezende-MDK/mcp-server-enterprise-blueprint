"""Handler determinístico para a ferramenta 'auth' com persistência em Redis."""

import os
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


def _get_admin_bootstrap_credentials(input_data: AuthInput) -> tuple[str, str, str]:
    """Obtém credenciais para o bootstrap do Admin a partir dos parâmetros de entrada ou variáveis de ambiente."""
    name = (input_data.name or "").strip() or os.environ.get("ADMIN_NAME", "Admin Master")
    email = (input_data.email or "").strip() or os.environ.get("ADMIN_EMAIL", "admin@empresa.com")
    token = (input_data.token or "").strip() or os.environ.get("ADMIN_TOKEN", "")
    if not token:
        token = generate_secure_token()
    return name, email, token


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
            role="lead",
        ).model_dump()

    # 2. SETUP E RESET TOTAL DO REDIS (BOOTSTRAP ADMIN)
    if action in (AuthAction.SETUP, AuthAction.RESET):
        # A) Limpar todas as chaves de autenticação antigas
        keys_res = execute_redis({"action": "keys", "pattern": "auth:*"})
        deleted_count = 0
        if keys_res.get("success") and isinstance(keys_res.get("keys"), list):
            for k in keys_res.get("keys"):
                del_res = execute_redis({"action": "del", "key": k})
                if del_res.get("success"):
                    deleted_count += 1
        
        # Garante remoção de chaves fixas
        execute_redis({"action": "del", "key": "auth:users:index"})

        # B) Criar usuário Admin Master no Redis
        admin_name, admin_email, admin_token = _get_admin_bootstrap_credentials(input_data)
        now = datetime.now(timezone.utc).isoformat()
        admin_data = {
            "name": admin_name,
            "email": admin_email,
            "token": admin_token,
            "role": "admin",
            "provider": "local",
            "google_id": "",
            "status": "active",
            "created_at": now,
            "last_login_at": now,
        }

        # 1. Salva o Hash do Admin no Redis
        execute_redis({
            "action": "hset",
            "key": f"auth:user:{admin_email}",
            "fields": admin_data,
        })

        # 2. Salva o índice de busca rápida O(1) por Token no Redis
        execute_redis({
            "action": "set",
            "key": f"auth:token:{admin_token}",
            "value": admin_data,
        })

        # 3. Registra no Set de Usuários
        execute_redis({
            "action": "sadd",
            "key": "auth:users:index",
            "member": admin_email,
        })

        return AuthOutput(
            success=True,
            action=action.value,
            message=f"Infraestrutura de autenticação resetada ({deleted_count} chaves limpas). Usuário Admin '{admin_name}' ({admin_email}) inicializado no Redis.",
            token=admin_token,
            role="admin",
            user=admin_data,
            is_valid=True,
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

        # Define a role: se explicitamente passado no input (ex: 'admin' ou 'lead') usa ele, senão o padrão é 'lead'
        admin_email_env = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        role = input_data.role or ("admin" if (admin_email_env and email == admin_email_env) else "lead")

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
            "role": role,
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

        # 2. Salva o índice de busca rápida O(1) por Token no Redis
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
            message=f"Usuário '{name}' ({email}) registrado com perfil '{role}' e token ativado com sucesso.",
            token=token,
            role=role,
            user=user_data,
        ).model_dump()

    # 4. VALIDAÇÃO E CONSULTA DE TOKEN (GET_TOKEN)
    if action == AuthAction.GET_TOKEN:
        token = (input_data.token or "").strip()
        email = (input_data.email or "").strip().lower()

        # A) Consulta por Token no Redis O(1)
        if token:
            token_res = execute_redis({"action": "get", "key": f"auth:token:{token}"})
            user_data = token_res.get("result")

            if user_data and isinstance(user_data, dict) and user_data.get("status") == "active":
                role = user_data.get("role") or "lead"
                return AuthOutput(
                    success=True,
                    action=action.value,
                    message="Token autenticado e ativo no perímetro.",
                    token=token,
                    role=role,
                    user=user_data,
                    is_valid=True,
                ).model_dump()

            return AuthOutput(
                success=True,
                action=action.value,
                message="Token não encontrado ou inativo.",
                token=token,
                role=None,
                user=None,
                is_valid=False,
            ).model_dump()

        # B) Consulta por E-mail no Redis O(1)
        if email:
            user_res = execute_redis({"action": "hgetall", "key": f"auth:user:{email}"})
            user_data = user_res.get("data") or {}

            if user_data and user_data.get("status") == "active":
                role = user_data.get("role") or "lead"
                return AuthOutput(
                    success=True,
                    action=action.value,
                    message=f"Usuário '{email}' localizado com sucesso.",
                    token=user_data.get("token"),
                    role=role,
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
