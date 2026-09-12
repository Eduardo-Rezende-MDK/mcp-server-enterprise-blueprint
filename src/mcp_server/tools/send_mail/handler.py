"""Handler determinístico para a ferramenta 'send_mail' (Gmail / SMTP / Mock Fallback)."""

import os
import re
import secrets
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Tuple
from .schema import SendMailInput, SendMailOutput


def _load_env_file() -> None:
    """Carrega variáveis do arquivo .env se ainda não presentes no ambiente."""
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


def _validate_email(email: str) -> bool:
    """Valida formato básico de endereço de e-mail."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, (email or "").strip()))


def build_email_content(recipient_name: str, token: str, server_url: str) -> Tuple[str, str]:
    """Gera versões em texto puro e HTML multipart para o e-mail de entrega de credenciais."""
    safe_name = recipient_name.strip()
    safe_url = server_url.rstrip("/")

    # Versão em Texto Puro
    plain_text = f"""Olá, {safe_name}!

Sua chave de acesso ao MCP Server Enterprise foi gerada com sucesso.

==================================================
🔑 SUA CHAVE BEARER (TOKEN DE ACESSO):
{token}
==================================================

🌐 Servidor: {safe_url}
📖 Endpoints:
- JSON-RPC 2.0: POST {safe_url}/
- SSE: GET {safe_url}/sse

COMO CONFIGURAR NO CLAUDE DESKTOP:
Adicione ao seu claude_desktop_config.json:

{{
  "mcpServers": {{
    "enterprise": {{
      "url": "{safe_url}",
      "headers": {{
        "Authorization": "Bearer {token}"
      }}
    }}
  }}
}}

Guarde esta chave em segurança. Ela concede acesso às ferramentas corporativas.
Equipe MCP Server Enterprise
"""

    # Versão em HTML Moderno
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sua Chave de Acesso · MCP Server Enterprise</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0F172A;
      color: #F8FAFC;
      margin: 0;
      padding: 24px 12px;
    }}
    .container {{
      max-width: 600px;
      margin: 0 auto;
      background-color: #1E293B;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .header {{
      background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
      padding: 32px 24px;
      text-align: center;
    }}
    .logo {{
      width: 48px;
      height: 48px;
      margin-bottom: 12px;
    }}
    .title {{
      color: #FFFFFF;
      font-size: 22px;
      font-weight: 700;
      margin: 0;
      letter-spacing: -0.02em;
    }}
    .subtitle {{
      color: #DBEAFE;
      font-size: 14px;
      margin-top: 6px;
    }}
    .content {{
      padding: 32px 24px;
    }}
    .greeting {{
      font-size: 16px;
      color: #E2E8F0;
      line-height: 1.6;
    }}
    .token-card {{
      background-color: #0F172A;
      border: 1px solid #3B82F6;
      border-radius: 12px;
      padding: 20px;
      margin: 24px 0;
      text-align: center;
    }}
    .token-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #94A3B8;
      margin-bottom: 8px;
      font-weight: 600;
    }}
    .token-value {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 15px;
      font-weight: 700;
      color: #60A5FA;
      word-break: break-all;
      background-color: rgba(37, 99, 235, 0.15);
      padding: 12px;
      border-radius: 8px;
      display: inline-block;
      margin: 0;
    }}
    .section-title {{
      font-size: 14px;
      font-weight: 600;
      color: #94A3B8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 24px;
      margin-bottom: 8px;
    }}
    .code-block {{
      background-color: #090D16;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 14px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      color: #CBD5E1;
      overflow-x: auto;
      white-space: pre;
    }}
    .footer {{
      background-color: #0F172A;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding: 20px 24px;
      text-align: center;
      font-size: 12px;
      color: #64748B;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 class="title">Chave de Acesso MCP</h1>
      <div class="subtitle">Servidor Enterprise · MardukaSoft</div>
    </div>
    <div class="content">
      <p class="greeting">Olá, <strong>{safe_name}</strong>!</p>
      <p class="greeting">Sua chave de acesso ao ecossistema <strong>MCP Server Enterprise</strong> foi emitida e vinculada com sucesso à sua conta.</p>
      
      <div class="token-card">
        <div class="token-label">Sua Chave Bearer (Token de Acesso)</div>
        <div class="token-value">{token}</div>
      </div>

      <div class="section-title">Snippet de Configuração (Claude Desktop / Cursor)</div>
      <div class="code-block">{{
  "mcpServers": {{
    "enterprise": {{
      "url": "{safe_url}",
      "headers": {{
        "Authorization": "Bearer {token}"
      }}
    }}
  }}
}}</div>
    </div>
    <div class="footer">
      Esta mensagem contém credenciais sensíveis de acesso. Guarde-a em segurança.<br>
      © 2026 MCP Server Enterprise · Todos os direitos reservados.
    </div>
  </div>
</body>
</html>
"""
    return plain_text, html_content


def execute(params: Dict[str, Any] | SendMailInput) -> Dict[str, Any]:
    """Executa o disparo transacional do e-mail com as credenciais do usuário."""
    _load_env_file()

    if isinstance(params, dict):
        input_data = SendMailInput(**params)
    else:
        input_data = params

    to_email = input_data.to_email.strip().lower()
    recipient_name = input_data.recipient_name.strip()
    token = input_data.token.strip()
    subject = input_data.subject or "Sua Chave de Acesso · MCP Server Enterprise"
    server_url = input_data.server_url or "https://mcp-server-enterprise.mardukasoft.online"

    now_iso = datetime.now(timezone.utc).isoformat()

    # Validação de e-mail
    if not _validate_email(to_email):
        return SendMailOutput(
            success=False,
            message="Endereço de e-mail inválido ou malformado.",
            delivery_mode="validation_failed",
            timestamp=now_iso,
            error=f"E-mail inválido: '{to_email}'",
        ).model_dump()

    # Validação de token
    if not token:
        return SendMailOutput(
            success=False,
            message="O token de acesso não pode ser vazio.",
            delivery_mode="validation_failed",
            timestamp=now_iso,
            error="Token ausente",
        ).model_dump()

    # Credenciais do Gmail / SMTP
    gmail_user = os.environ.get("GMAIL_USER", "").strip() or os.environ.get("SMTP_USER", "").strip()
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip() or os.environ.get("SMTP_PASSWORD", "").strip()

    # Se credenciais ausentes no ambiente, reporta explicitamente a falha (sem falso positivo)
    if not gmail_user or not gmail_password:
        return SendMailOutput(
            success=False,
            message="Credenciais de e-mail não configuradas no servidor (GMAIL_USER / GMAIL_APP_PASSWORD ausentes).",
            delivery_mode="unconfigured",
            timestamp=now_iso,
            error="Credenciais SMTP ausentes no ambiente",
        ).model_dump()

    plain_text, html_content = build_email_content(recipient_name, token, server_url)

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"MCP Enterprise Server <{gmail_user}>"
        msg["To"] = to_email
        message_id = f"<{int(time.time())}.{secrets.token_hex(8)}@{gmail_user.split('@')[-1]}>"
        msg["Message-ID"] = message_id

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)

        return SendMailOutput(
            success=True,
            message=f"E-mail transacional enviado com sucesso via Gmail para '{to_email}'.",
            message_id=message_id,
            delivery_mode="gmail_smtp",
            timestamp=now_iso,
        ).model_dump()

    except Exception as exc:
        return SendMailOutput(
            success=False,
            message=f"Falha no envio do e-mail para '{to_email}' via SMTP.",
            delivery_mode="smtp_failed",
            timestamp=now_iso,
            error=f"Erro SMTP: {exc}",
        ).model_dump()
