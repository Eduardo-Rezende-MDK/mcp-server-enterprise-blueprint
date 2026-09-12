"""Unit tests for the 'send_mail' MCP tool (Strict SMTP & No False Positives)."""

import os
import smtplib
from unittest.mock import MagicMock, patch
import pytest
from mcp_server.registry import dispatch_tool
from mcp_server.tools.send_mail.handler import build_email_content


def test_send_mail_unconfigured_credentials(monkeypatch):
    """Valida rejeição determinística (success=False) quando as credenciais SMTP estão ausentes."""
    monkeypatch.setenv("GMAIL_USER", "")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "")
    monkeypatch.setenv("SMTP_USER", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")

    res = dispatch_tool("send_mail", {
        "to_email": "lead.teste@empresa.com",
        "recipient_name": "Eduardo Rezende",
        "token": "mcp_live_e8471b045e758763118cfbf5ec94a02c",
    })
    assert res["success"] is False
    assert res["delivery_mode"] == "unconfigured"
    assert "não configuradas" in res["message"].lower() or "ausentes" in res["error"].lower()
    assert res["error"] is not None


def test_send_mail_smtp_success(monkeypatch):
    """Valida envio real via Gmail SMTP com sucesso usando mock do socket/cliente SMTP."""
    monkeypatch.setenv("GMAIL_USER", "server@empresa.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password-secret-123")

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    with patch("smtplib.SMTP_SSL", return_value=mock_smtp_instance) as mock_ssl:
        res = dispatch_tool("send_mail", {
            "to_email": "lead.teste@empresa.com",
            "recipient_name": "Eduardo Rezende",
            "token": "mcp_live_e8471b045e758763118cfbf5ec94a02c",
        })

        assert res["success"] is True
        assert res["delivery_mode"] == "gmail_smtp"
        assert "sucesso" in res["message"].lower()
        assert res["message_id"] is not None
        assert "@empresa.com>" in res["message_id"]

        mock_ssl.assert_called_once_with("smtp.gmail.com", 465, timeout=10)
        mock_smtp_instance.login.assert_called_once_with("server@empresa.com", "app-password-secret-123")
        mock_smtp_instance.send_message.assert_called_once()


def test_send_mail_smtp_failure(monkeypatch):
    """Valida que falhas reais de conexão/autenticação SMTP retornam success=False sem falso positivo."""
    monkeypatch.setenv("GMAIL_USER", "server@empresa.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "app-password-secret-123")

    with patch("smtplib.SMTP_SSL", side_effect=smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")):
        res = dispatch_tool("send_mail", {
            "to_email": "lead.teste@empresa.com",
            "recipient_name": "Eduardo Rezende",
            "token": "mcp_live_e8471b045e758763118cfbf5ec94a02c",
        })

        assert res["success"] is False
        assert res["delivery_mode"] == "smtp_failed"
        assert "Erro SMTP" in res["error"]
        assert "Falha" in res["message"]


def test_send_mail_html_and_text_template():
    """Valida a construção dos templates de e-mail (HTML e Texto puro)."""
    name = "Ana Beatriz"
    token = "mcp_live_test_token_123"
    server_url = "https://mcp-server-enterprise.mardukasoft.online"

    plain, html = build_email_content(name, token, server_url)

    # Validações no Texto Puro
    assert name in plain
    assert token in plain
    assert server_url in plain
    assert "claude_desktop_config.json" in plain

    # Validações no HTML
    assert name in html
    assert token in html
    assert "Chave de Acesso MCP" in html
    assert "token-value" in html
    assert "<!DOCTYPE html>" in html


def test_send_mail_invalid_email():
    """Valida rejeição determinística para e-mails malformados."""
    res = dispatch_tool("send_mail", {
        "to_email": "email_invalido_sem_formato",
        "recipient_name": "Nome Valido",
        "token": "mcp_live_123",
    })
    assert res["success"] is False
    assert res["delivery_mode"] == "validation_failed"
    assert "inválido" in res["message"].lower() or "e-mail" in res["error"].lower()


def test_send_mail_empty_token():
    """Valida rejeição para token ausente ou vazio."""
    res = dispatch_tool("send_mail", {
        "to_email": "lead@empresa.com",
        "recipient_name": "Nome Valido",
        "token": "   ",
    })
    assert res["success"] is False
    assert res["delivery_mode"] == "validation_failed"
    assert "token" in res["error"].lower() or "token" in res["message"].lower()


def test_send_mail_custom_subject_and_server(monkeypatch):
    """Valida personalização de assunto e URL do servidor em envio SMTP."""
    monkeypatch.setenv("GMAIL_USER", "admin@mardukasoft.online")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret123")

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance

    with patch("smtplib.SMTP_SSL", return_value=mock_smtp_instance):
        custom_subject = "Seu Acesso VIP ao MCP"
        custom_url = "https://custom.mcp.marduka.io"

        res = dispatch_tool("send_mail", {
            "to_email": "vip@empresa.com",
            "recipient_name": "VIP User",
            "token": "mcp_live_vip_token_999",
            "subject": custom_subject,
            "server_url": custom_url,
        })
        assert res["success"] is True
        assert res["delivery_mode"] == "gmail_smtp"
