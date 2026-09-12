"""Unit tests for the 'auth' MCP tool with Redis persistence."""

import pytest
from mcp_server.registry import dispatch_tool


def test_auth_token_generator():
    """Valida a geração de tokens criptográficos com prefixo mcp_live_."""
    res = dispatch_tool("auth", {"action": "token_generator"})
    assert res["success"] is True
    assert res["token"].startswith("mcp_live_")
    assert len(res["token"]) == len("mcp_live_") + 32  # 16 bytes hex = 32 chars


def test_auth_setup():
    """Valida o handshake de setup e bootstrap do admin com persistência em Redis."""
    res = dispatch_tool("auth", {
        "action": "setup",
        "name": "Admin Teste",
        "email": "admin@teste.com",
        "token": "mcp_admin_test_12345",
    })
    assert res["success"] is True
    assert res["role"] == "admin"
    assert res["token"] == "mcp_admin_test_12345"
    assert res["user"]["email"] == "admin@teste.com"
    assert res["user"]["role"] == "admin"


def test_auth_set_token_and_get_token():
    """Valida o cadastro de usuário com Nome e E-mail e subsequente validação de token e role."""
    user_email = "lead.enterprise@empresa.com"
    user_name = "Eduardo Rezende"

    # 1. Cadastra usuário e gera token com role lead
    set_res = dispatch_tool("auth", {
        "action": "set_token",
        "name": user_name,
        "email": user_email,
        "provider": "local",
    })
    assert set_res["success"] is True
    assert set_res["token"].startswith("mcp_live_")
    assert set_res["role"] == "lead"
    assert set_res["user"]["name"] == user_name
    assert set_res["user"]["email"] == user_email
    assert set_res["user"]["role"] == "lead"
    assert set_res["user"]["status"] == "active"

    generated_token = set_res["token"]

    # 2. Valida o token gerado via get_token
    get_res = dispatch_tool("auth", {
        "action": "get_token",
        "token": generated_token,
    })
    assert get_res["success"] is True
    assert get_res["is_valid"] is True
    assert get_res["user"]["name"] == user_name
    assert get_res["user"]["email"] == user_email


def test_auth_get_token_by_email():
    """Valida a recuperação de dados e token ativo a partir do e-mail."""
    user_email = "consulta.lead@empresa.com"
    user_name = "Carlos Drummond"

    set_res = dispatch_tool("auth", {
        "action": "set_token",
        "name": user_name,
        "email": user_email,
    })
    token = set_res["token"]

    # Consulta por e-mail
    query_res = dispatch_tool("auth", {
        "action": "get_token",
        "email": user_email,
    })
    assert query_res["success"] is True
    assert query_res["is_valid"] is True
    assert query_res["token"] == token
    assert query_res["user"]["name"] == user_name


def test_auth_unregistered_token_is_rejected():
    """Valida que qualquer token não cadastrado previamente no Redis é rejeitado."""
    res = dispatch_tool("auth", {
        "action": "get_token",
        "token": "token_nao_cadastrado_qualquer",
    })
    assert res["success"] is True
    assert res["is_valid"] is False
    assert res["user"] is None


def test_auth_invalid_token():
    """Valida que token inexistente retorna is_valid=False."""
    res = dispatch_tool("auth", {
        "action": "get_token",
        "token": "mcp_live_token_inexistente_123456789",
    })
    assert res["success"] is True
    assert res["is_valid"] is False
    assert res["user"] is None


def test_auth_validation_errors():
    """Valida rejeição de inputs inválidos no cadastro."""
    # Sem nome
    res_no_name = dispatch_tool("auth", {
        "action": "set_token",
        "email": "semnome@empresa.com",
    })
    assert res_no_name["success"] is False
    assert "Nome" in res_no_name["error"] or "name" in res_no_name["message"]

    # E-mail inválido
    res_bad_email = dispatch_tool("auth", {
        "action": "set_token",
        "name": "Nome Valido",
        "email": "email_invalido_sem_arroba",
    })
    assert res_bad_email["success"] is False
    assert "inválido" in res_bad_email["message"].lower() or "e-mail" in res_bad_email["error"].lower()
