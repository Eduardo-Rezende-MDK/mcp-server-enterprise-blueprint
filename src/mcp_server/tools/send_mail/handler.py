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
    """Carrega variáveis do arquivo .env se ainda não presentes ou atualizadas."""
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


def _validate_email(email: str) -> bool:
    """Valida formato básico de endereço de e-mail."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, (email or "").strip()))


def build_email_content(recipient_name: str, token: str, server_url: str) -> Tuple[str, str]:
    """Gera versões em texto puro e HTML multipart para o e-mail de entrega de credenciais com snippets para os principais LLMs."""
    safe_name = recipient_name.strip()
    safe_url = server_url.rstrip("/")

    # Versão em Texto Puro
    plain_text = f"""Olá, {safe_name}!

Sua chave de acesso ao ecossistema MCP Server Enterprise foi gerada e vinculada com sucesso.

==================================================
🔑 SUA CHAVE BEARER (TOKEN DE ACESSO):
{token}
==================================================

🌐 Servidor: {safe_url}
📖 Endpoints MCP:
- JSON-RPC 2.0: POST {safe_url}/
- SSE: GET {safe_url}/sse

--------------------------------------------------
📋 SNIPPETS DE CONFIGURAÇÃO PARA OS PRINCIPAIS LLMs:
--------------------------------------------------

1. 🤖 CLAUDE DESKTOP (claude_desktop_config.json):
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

2. ⚡ CURSOR AI (.cursor/mcp.json ou Cursor Settings -> MCP):
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

3. 🌊 WINDSURF / CASCADE (~/.codeium/windsurf/mcp_config.json):
{{
  "mcpServers": {{
    "enterprise": {{
      "serverUrl": "{safe_url}",
      "headers": {{
        "Authorization": "Bearer {token}"
      }}
    }}
  }}
}}

4. 🐍 PYTHON / FRAMEWORKS DE AGENTES (LangChain, CrewAI, AutoGen, LlamaIndex):
import httpx

client = httpx.Client(
    base_url="{safe_url}",
    headers={{"Authorization": "Bearer {token}"}}
)
response = client.post("/", json={{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}})
print(response.json())

5. 💻 cURL / TERMINAL:
curl -X POST {safe_url}/ \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json" \\
  -d '{{"jsonrpc":"2.0","id":1,"method":"tools/list"}}'

Guarde esta chave em segurança. Ela concede acesso a todas as ferramentas corporativas.
Equipe MCP Server Enterprise · MardukaSoft
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
      max-width: 640px;
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
    .snippet-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 24px;
      margin-bottom: 8px;
    }}
    .badge {{
      background-color: #334155;
      color: #38BDF8;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .snippet-title {{
      font-size: 13px;
      font-weight: 700;
      color: #94A3B8;
      text-transform: uppercase;
      letter-spacing: 0.05em;
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
      line-height: 1.5;
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
      <p class="greeting">Sua chave de acesso ao ecossistema <strong>MCP Server Enterprise</strong> foi emitida com sucesso.</p>
      
      <div class="token-card">
        <div class="token-label">Sua Chave Bearer (Token de Acesso)</div>
        <div class="token-value">{token}</div>
      </div>

      <!-- 1. Claude Desktop -->
      <div class="snippet-header">
        <span class="snippet-title">🤖 1. Claude Desktop</span>
        <span class="badge">claude_desktop_config.json</span>
      </div>
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

      <!-- 2. Cursor AI -->
      <div class="snippet-header">
        <span class="snippet-title">⚡ 2. Cursor AI</span>
        <span class="badge">.cursor/mcp.json</span>
      </div>
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

      <!-- 3. Windsurf / Cascade -->
      <div class="snippet-header">
        <span class="snippet-title">🌊 3. Windsurf / Codeium Cascade</span>
        <span class="badge">mcp_config.json</span>
      </div>
      <div class="code-block">{{
  "mcpServers": {{
    "enterprise": {{
      "serverUrl": "{safe_url}",
      "headers": {{
        "Authorization": "Bearer {token}"
      }}
    }}
  }}
}}</div>

      <!-- 4. Python SDK / Agentes -->
      <div class="snippet-header">
        <span class="snippet-title">🐍 4. Python / LangChain / CrewAI / AutoGen</span>
        <span class="badge">Python 3</span>
      </div>
      <div class="code-block">import httpx

client = httpx.Client(
    base_url="{safe_url}",
    headers={{"Authorization": "Bearer {token}"}}
)
response = client.post("/", json={{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}})
print(response.json())</div>

      <!-- 5. cURL / Terminal -->
      <div class="snippet-header">
        <span class="snippet-title">💻 5. cURL / Terminal</span>
        <span class="badge">Bash / Zsh / PowerShell</span>
      </div>
      <div class="code-block">curl -X POST {safe_url}/ \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json" \\
  -d '{{"jsonrpc":"2.0","id":1,"method":"tools/list"}}'</div>
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


try:
    from js import Headers as js_Headers, Object as js_Object, fetch as js_fetch
except ImportError:
    js_fetch = None


async def execute_async(params: Dict[str, Any] | SendMailInput) -> Dict[str, Any]:
    """Versão assíncrona otimizada para o Cloudflare Workers Edge (usando js.fetch nativo)."""
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

    if not _validate_email(to_email):
        return SendMailOutput(
            success=False,
            message="Endereço de e-mail inválido ou malformado.",
            delivery_mode="validation_failed",
            timestamp=now_iso,
            error=f"E-mail inválido: '{to_email}'",
        ).model_dump()

    if not token:
        return SendMailOutput(
            success=False,
            message="O token de acesso não pode ser vazio.",
            delivery_mode="validation_failed",
            timestamp=now_iso,
            error="Token ausente",
        ).model_dump()

    plain_text, html_content = build_email_content(recipient_name, token, server_url)

    # 1. Resend API via js.fetch (Cloudflare Edge Native)
    resend_api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_api_key:
        if js_fetch is not None:
            try:
                import json
                sender_email = os.environ.get("RESEND_FROM", "MCP Server Enterprise <acesso@mardukasoft.online>").strip()
                payload_str = json.dumps({
                    "from": sender_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content,
                    "text": plain_text,
                })

                hdrs = js_Headers.new()
                hdrs.set("Authorization", f"Bearer {resend_api_key}")
                hdrs.set("Content-Type", "application/json")
                hdrs.set("User-Agent", "MCP-Enterprise-Server/1.0")

                opts = js_Object.new()
                opts.method = "POST"
                opts.headers = hdrs
                opts.body = payload_str

                resp = await js_fetch("https://api.resend.com/emails", opts)
                resp_text = await resp.text()

                if resp.status in (200, 201):
                    res_data = json.loads(resp_text)
                    return SendMailOutput(
                        success=True,
                        message=f"E-mail transacional enviado com sucesso via Resend para '{to_email}'.",
                        message_id=res_data.get("id"),
                        delivery_mode="resend_api",
                        timestamp=now_iso,
                    ).model_dump()
                else:
                    return SendMailOutput(
                        success=False,
                        message=f"Falha na API do Resend (status {resp.status}) ao enviar para '{to_email}'.",
                        delivery_mode="resend_api_failed",
                        timestamp=now_iso,
                        error=f"Resend HTTP {resp.status}: {resp_text}",
                    ).model_dump()
            except Exception as exc:
                return SendMailOutput(
                    success=False,
                    message=f"Erro no disparo via Resend Edge: {str(exc)}",
                    delivery_mode="resend_api_failed",
                    timestamp=now_iso,
                    error=str(exc),
                ).model_dump()
        else:
            return execute(params)

    # 2. Fallback padrão síncrono
    return execute(params)


def execute(params: Dict[str, Any] | SendMailInput) -> Dict[str, Any]:
    """Executa o disparo transacional do e-mail com as credenciais do usuário."""

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

    plain_text, html_content = build_email_content(recipient_name, token, server_url)

    # 1. Suporte a Resend API (HTTP REST Edge-Native)
    resend_api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_api_key:
        try:
            import json
            import urllib.error
            import urllib.request
            sender_email = os.environ.get("RESEND_FROM", "MCP Server Enterprise <acesso@mardukasoft.online>").strip()
            payload = json.dumps({
                "from": sender_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": plain_text,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=payload,
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "MCP-Enterprise-Server/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return SendMailOutput(
                    success=True,
                    message=f"E-mail transacional enviado com sucesso via Resend para '{to_email}'.",
                    message_id=res_data.get("id"),
                    delivery_mode="resend_api",
                    timestamp=now_iso,
                ).model_dump()
        except urllib.error.HTTPError as http_err:
            try:
                err_body = http_err.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("message") or err_body
            except Exception:
                err_msg = str(http_err)
            return SendMailOutput(
                success=False,
                message=f"Falha na API do Resend ao enviar para '{to_email}'.",
                delivery_mode="resend_api_failed",
                timestamp=now_iso,
                error=f"Resend API Error ({http_err.code}): {err_msg}",
            ).model_dump()
        except Exception as exc:
            return SendMailOutput(
                success=False,
                message=f"Erro de conexão com a API do Resend ao enviar para '{to_email}'.",
                delivery_mode="resend_api_failed",
                timestamp=now_iso,
                error=f"Resend Exception: {str(exc)}",
            ).model_dump()


    # 2. Suporte a Brevo API (HTTP REST Edge-Native)
    brevo_api_key = os.environ.get("BREVO_API_KEY", "").strip()
    if brevo_api_key:
        try:
            import json
            import urllib.request
            sender_email = os.environ.get("BREVO_FROM_EMAIL", "dev@exemplo.com").strip()
            sender_name = os.environ.get("BREVO_FROM_NAME", "MCP Server Enterprise").strip()
            payload = json.dumps({
                "sender": {"name": sender_name, "email": sender_email},
                "to": [{"email": to_email, "name": recipient_name}],
                "subject": subject,
                "htmlContent": html_content,
                "textContent": plain_text,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=payload,
                headers={
                    "api-key": brevo_api_key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return SendMailOutput(
                    success=True,
                    message=f"E-mail transacional enviado com sucesso via Brevo para '{to_email}'.",
                    message_id=res_data.get("messageId"),
                    delivery_mode="brevo_api",
                    timestamp=now_iso,
                ).model_dump()
        except Exception as exc:
            pass

    # 3. Credenciais do Gmail / SMTP (TCP Socket - Local / Node / Python)
    gmail_user = os.environ.get("GMAIL_USER", "").strip() or os.environ.get("SMTP_USER", "").strip()
    raw_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip() or os.environ.get("SMTP_PASSWORD", "").strip()
    gmail_password = raw_password.replace(" ", "")

    if not gmail_user or not gmail_password:
        return SendMailOutput(
            success=False,
            message="Credenciais de e-mail não configuradas no servidor (GMAIL_USER / GMAIL_APP_PASSWORD ausentes).",
            delivery_mode="unconfigured",
            timestamp=now_iso,
            error="Credenciais SMTP ausentes no ambiente",
        ).model_dump()

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
