"""Integration tests for Portal Web UI and Authentication REST Handlers."""

import pytest
from mcp_server.registry import dispatch_tool
from mcp_server.security import validate_bearer_token
from mcp_server.ui.portal import get_portal_html, handle_google_login, handle_lead_login


def test_get_portal_html_contains_essential_elements():
    """Valida se o template HTML do portal contém os componentes visuais obrigatórios."""
    html = get_portal_html()
    assert "<!DOCTYPE html>" in html
    assert "MCP SERVER ENTERPRISE" in html
    assert "Autorização de Acesso" in html
    assert 'id="nameInput"' in html
    assert 'id="emailInput"' in html
    assert "Sign in with Google" in html
    assert "/api/auth/login" in html
    assert "/api/auth/google" in html


def test_handle_lead_login_flow():
    """Valida o fluxo completo de cadastro de lead (Nome + E-mail -> Redis -> send_mail)."""
    lead_name = "Roberta Miranda"
    lead_email = "roberta.miranda@empresa.com"

    res = handle_lead_login({"name": lead_name, "email": lead_email})
    assert res["success"] is True
    # Garante que o token NÃO é vazado no payload público retornado
    assert "token" not in res
    assert "token" not in res["user"]
    assert res["user"]["name"] == lead_name
    assert res["user"]["email"] == lead_email
    assert res["user"]["status"] == "active"
    assert res["mail_status"] is not None

    # Consulta o token persistido internamente no Redis via Tool 'auth'
    auth_check = dispatch_tool("auth", {"action": "get_token", "email": lead_email})
    assert auth_check["success"] is True
    assert auth_check["is_valid"] is True
    token = auth_check["token"]
    assert token.startswith("mcp_live_")

    # Garante que o token emitido já é aceito no perímetro de segurança
    assert validate_bearer_token(f"Bearer {token}") is True


def test_handle_lead_login_validation_failure():
    """Valida rejeição quando faltam campos obrigatórios."""
    res_no_name = handle_lead_login({"email": "alguem@empresa.com"})
    assert res_no_name["success"] is False
    assert "obrigatórios" in res_no_name["error"]

    res_no_email = handle_lead_login({"name": "Nome Teste"})
    assert res_no_email["success"] is False
    assert "obrigatórios" in res_no_email["error"]


def test_handle_google_login_flow():
    """Valida o fluxo de autenticação social com Google."""
    google_name = "Dev Google SSO"
    google_email = "dev.sso@gmail.com"
    google_id = "google_user_987654321"

    res = handle_google_login({
        "name": google_name,
        "email": google_email,
        "google_id": google_id,
    })
    assert res["success"] is True
    # Garante que o token NÃO é exposto na resposta da requisição pública
    assert "token" not in res
    assert "token" not in res["user"]
    assert res["user"]["provider"] == "google"
    assert res["user"]["google_id"] == google_id

    # Consulta o token persistido internamente no Redis via Tool 'auth'
    auth_check = dispatch_tool("auth", {"action": "get_token", "email": google_email})
    assert auth_check["success"] is True
    assert auth_check["is_valid"] is True
    token = auth_check["token"]
    assert token.startswith("mcp_live_")

    # Garante que o token Google também é validado no perímetro
    assert validate_bearer_token(f"Bearer {token}") is True
