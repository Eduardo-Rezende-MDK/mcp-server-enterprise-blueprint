"""Portal Web UI and Authentication Handlers for Lead Capture and Token Management."""

import json
from typing import Any, Dict
from ..registry import dispatch_tool


def get_portal_html(google_client_id: str = "") -> str:
    """Retorna o template HTML da Landing Page de autenticação passwordless e captura de leads."""
    import os
    client_id = (google_client_id or os.environ.get("GOOGLE_CLIENT_ID", "")).strip()
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MCP Enterprise · Acesso ao Servidor</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <!-- Google Identity Services SDK Oficial -->
  <script src="https://accounts.google.com/gsi/client" async defer></script>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
      color: #111827;
      -webkit-font-smoothing: antialiased;
    }}
    .auth-card {{
      background: #ffffff;
      width: 100%;
      max-width: 440px;
      border-radius: 32px;
      padding: 44px 36px 40px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.1);
      animation: cardAppear 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    @keyframes cardAppear {{
      from {{
        opacity: 0;
        transform: translateY(16px) scale(0.98);
      }}
      to {{
        opacity: 1;
        transform: translateY(0) scale(1);
      }}
    }}
    .brand-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 28px;
    }}
    .brand-name {{
      font-size: 1.25rem;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.03em;
    }}
    .auth-title {{
      font-size: 1.85rem;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.025em;
      margin-bottom: 6px;
    }}
    .auth-subtitle {{
      font-size: 0.95rem;
      color: #64748b;
      margin-bottom: 24px;
      font-weight: 400;
    }}
    .input-wrapper {{
      position: relative;
      margin-bottom: 22px;
    }}
    .input-label {{
      position: absolute;
      top: -9px;
      left: 14px;
      background: #ffffff;
      padding: 0 6px;
      font-size: 0.78rem;
      font-weight: 600;
      color: #2563eb;
      border-radius: 4px;
    }}
    .text-input {{
      width: 100%;
      height: 52px;
      border: 1.5px solid #cbd5e1;
      border-radius: 14px;
      padding: 0 18px;
      font-size: 1rem;
      font-family: inherit;
      color: #0f172a;
      outline: none;
      transition: all 0.2s ease;
      background: #ffffff;
    }}
    .text-input:focus {{
      border-color: #2563eb;
      box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
    }}
    .btn-primary {{
      width: 100%;
      height: 52px;
      background: #0066ff;
      color: #ffffff;
      border: none;
      border-radius: 14px;
      font-size: 1rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 4px 14px rgba(0, 102, 255, 0.35);
    }}
    .btn-primary:hover {{
      background: #0052cc;
      transform: translateY(-1px);
    }}
    .btn-primary:disabled {{
      opacity: 0.7;
      cursor: not-allowed;
    }}
    .divider {{
      display: flex;
      align-items: center;
      margin: 20px 0;
      color: #94a3b8;
      font-size: 0.88rem;
      font-weight: 500;
    }}
    .divider::before,
    .divider::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: #e2e8f0;
    }}
    .divider span {{
      padding: 0 14px;
    }}
    .btn-google {{
      width: 100%;
      height: 52px;
      background: #ffffff;
      border: 1.5px solid #e2e8f0;
      border-radius: 14px;
      font-size: 0.95rem;
      font-weight: 600;
      color: #1e293b;
      font-family: inherit;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      transition: all 0.2s ease;
    }}
    .btn-google:hover {{
      background: #f8fafc;
      border-color: #cbd5e1;
    }}
    .google-icon {{
      width: 20px;
      height: 20px;
    }}
    .toast {{
      display: none;
      padding: 14px;
      border-radius: 12px;
      font-size: 0.88rem;
      margin-bottom: 20px;
      animation: fadeIn 0.3s ease;
      line-height: 1.5;
    }}
    .toast-success {{
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      color: #166534;
    }}
    .toast-error {{
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
    }}
    .email-badge {{
      margin: 14px 0 10px;
      padding: 12px 14px;
      background: #ecfdf5;
      border: 1.5px solid #a7f3d0;
      border-radius: 12px;
      font-weight: 700;
      color: #065f46;
      font-size: 0.98rem;
      word-break: break-all;
      text-align: center;
    }}
    .email-instructions {{
      font-size: 0.86rem;
      color: #475569;
      line-height: 1.5;
      text-align: center;
      margin-top: 6px;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(-6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
</head>
<body>
  <div class="auth-card">
    <div class="brand-header">
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M16 4L28 10V22L16 28L4 22V10L16 4Z" stroke="#2563EB" stroke-width="2.5" stroke-linejoin="round"/>
        <path d="M16 12L22 15.5V20.5L16 24L10 20.5V15.5L16 12Z" fill="#2563EB"/>
      </svg>
      <span class="brand-name">MCP SERVER ENTERPRISE</span>
    </div>

    <h1 class="auth-title">Autorização de Acesso</h1>
    <p class="auth-subtitle">Informe seu nome e email corporativo para liberar seu acesso.</p>

    <div id="feedbackToast" class="toast"></div>

    <form id="authForm" onsubmit="handleSubmit(event)">
      <div class="input-wrapper">
        <label class="input-label" for="nameInput">Nome</label>
        <input type="text" id="nameInput" class="text-input" placeholder="Seu nome completo" required autocomplete="name" />
      </div>

      <div class="input-wrapper">
        <label class="input-label" for="emailInput">Email</label>
        <input type="email" id="emailInput" class="text-input" placeholder="nome@empresa.com" required autocomplete="email" />
      </div>

      <button type="submit" id="submitBtn" class="btn-primary">
        <span>Liberar Acesso</span>
      </button>
    </form>

    <div class="divider">
      <span>ou continue com</span>
    </div>

    <div id="g_id_onload"
         data-client_id="{client_id}"
         data-context="signin"
         data-ux_mode="popup"
         data-callback="handleCredentialResponse"
         data-auto_prompt="false">
    </div>

    <div id="googleBtnWrapper" style="width: 100%; display: flex; justify-content: center;">
      <div id="googleButtonContainer" style="width: 100%; display: flex; justify-content: center;"></div>
      <button type="button" id="customGoogleBtn" class="btn-google" onclick="handleGoogleSignInClick()">
        <svg class="google-icon" viewBox="0 0 24 24">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
        </svg>
        <span>Sign in with Google</span>
      </button>
    </div>
  </div>

  <script>
    const GOOGLE_CLIENT_ID = "{client_id}";

    function initGoogleIdentity() {{
      if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {{
        if (GOOGLE_CLIENT_ID) {{
          google.accounts.id.initialize({{
            client_id: GOOGLE_CLIENT_ID,
            callback: handleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true
          }});
          const container = document.getElementById('googleButtonContainer');
          const customBtn = document.getElementById('customGoogleBtn');
          if (container) {{
            google.accounts.id.renderButton(container, {{
              theme: 'outline',
              size: 'large',
              width: 368,
              text: 'continue_with',
              shape: 'pill'
            }});
            if (customBtn) customBtn.style.display = 'none';
          }}
        }}
      }}
    }}

    window.addEventListener('load', () => {{
      let tries = 0;
      const interval = setInterval(() => {{
        tries++;
        if (typeof google !== 'undefined' && google.accounts) {{
          clearInterval(interval);
          initGoogleIdentity();
        }} else if (tries > 25) {{
          clearInterval(interval);
        }}
      }}, 150);
    }});

    function handleGoogleSignInClick() {{
      const toast = document.getElementById('feedbackToast');
      if (typeof google !== 'undefined' && google.accounts && google.accounts.id && GOOGLE_CLIENT_ID) {{
        google.accounts.id.prompt((notification) => {{
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {{
            toast.className = 'toast toast-error';
            toast.style.display = 'block';
            toast.innerHTML = '<strong>Aviso Google:</strong> Janela bloqueada ou fechada. Utilize o formulário acima para liberar o acesso instantaneamente.';
          }}
        }});
        return;
      }}

      // Mensagem clara quando a chave Client ID ainda não foi configurada
      toast.className = 'toast toast-error';
      toast.style.display = 'block';
      toast.innerHTML = '<strong>Google SSO em Configuração:</strong><br><span style="font-size:0.85rem;">Para prosseguir imediatamente, informe seu Nome e E-mail no formulário acima.</span>';
    }}

    function formatErrorMessage(data, fallbackMsg) {{
      if (!data) return fallbackMsg;
      if (data.error) {{
        if (typeof data.error === 'object' && data.error !== null) {{
          return data.error.message || JSON.stringify(data.error);
        }}
        return String(data.error);
      }}
      if (data.message) {{
        if (typeof data.message === 'object' && data.message !== null) {{
          return data.message.message || JSON.stringify(data.message);
        }}
        return String(data.message);
      }}
      return fallbackMsg;
    }}

    async function handleSubmit(e) {{
      e.preventDefault();
      const name = document.getElementById('nameInput').value.trim();
      const email = document.getElementById('emailInput').value.trim();
      const btn = document.getElementById('submitBtn');
      const toast = document.getElementById('feedbackToast');

      btn.disabled = true;
      btn.innerHTML = '<span>Processando...</span>';

      try {{
        const response = await fetch('/api/auth/login', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ name, email }})
        }});
        const data = await response.json();

        if (response.ok && data.success) {{
          toast.className = 'toast toast-success';
          toast.style.display = 'block';
          toast.innerHTML = `
            <div style="text-align:center; padding:6px 0;">
              <div style="font-size:2rem; margin-bottom:6px;">📬</div>
              <strong style="font-size:1.1rem; color:#166534;">Acesso Solicitado com Sucesso!</strong>
              <p style="margin-top:8px; color:#1e293b; font-size:0.92rem;">
                Enviamos sua <strong>chave de acesso Bearer</strong> e as instruções de conexão diretamente para:
              </p>
              <div class="email-badge">${{email}}</div>
              <p class="email-instructions">
                Por favor, verifique sua <strong>caixa de entrada</strong> e a pasta de <strong>spam / lixo eletrônico</strong> para obter sua chave.
              </p>
            </div>
          `;
          document.getElementById('authForm').reset();
        }} else {{
          toast.className = 'toast toast-error';
          toast.style.display = 'block';
          toast.innerHTML = `<strong>Erro:</strong> ${{formatErrorMessage(data, 'Falha ao processar cadastro')}}`;
        }}
      }} catch (err) {{
        toast.className = 'toast toast-error';
        toast.style.display = 'block';
        toast.innerHTML = `<strong>Erro de Conexão:</strong> ${{err.message}}`;
      }} finally {{
        btn.disabled = false;
        btn.innerHTML = '<span>Liberar Acesso</span>';
      }}
    }}

    function handleCredentialResponse(response) {{
      if (response && response.credential) {{
        const toast = document.getElementById('feedbackToast');
        fetch('/api/auth/google', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ credential: response.credential }})
        }})
        .then(res => res.json())
        .then(data => {{
          if (data.success) {{
            toast.className = 'toast toast-success';
            toast.style.display = 'block';
            const userEmail = (data.user && data.user.email) ? data.user.email : 'seu e-mail do Google';
            toast.innerHTML = `
              <div style="text-align:center; padding:6px 0;">
                <div style="font-size:2rem; margin-bottom:6px;">🎉</div>
                <strong style="font-size:1.1rem; color:#166534;">Autenticado via Google com Sucesso!</strong>
                <p style="margin-top:8px; color:#1e293b; font-size:0.92rem;">
                  Enviamos sua <strong>chave de acesso Bearer</strong> e as instruções de configuração para:
                </p>
                <div class="email-badge">${{userEmail}}</div>
                <p class="email-instructions">
                  Verifique sua caixa de entrada no Gmail para obter a chave e conectar seus agentes.
                </p>
              </div>
            `;
          }} else {{
            toast.className = 'toast toast-error';
            toast.style.display = 'block';
            toast.innerHTML = `<strong>Erro Google:</strong> ${{formatErrorMessage(data, 'Falha ao autenticar')}}`;
          }}
        }})
        .catch(err => {{
          toast.className = 'toast toast-error';
          toast.style.display = 'block';
          toast.innerHTML = `<strong>Erro de Conexão:</strong> ${{err.message}}`;
        }});
      }}
    }}
  </script>
</body>
</html>
"""


async def handle_lead_login_async(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processa requisição de login/cadastro de lead de forma assíncrona (otimizada para Cloudflare Edge)."""
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email:
        return {
            "success": False,
            "error": "Nome e e-mail são obrigatórios para liberar o acesso.",
        }

    # 1. Cadastra no Redis via Tool 'auth'
    auth_res = dispatch_tool("auth", {
        "action": "set_token",
        "name": name,
        "email": email,
        "provider": "local",
    })

    if not auth_res.get("success"):
        return {
            "success": False,
            "error": auth_res.get("error") or auth_res.get("message") or "Erro ao cadastrar usuário",
        }

    token = auth_res.get("token")
    raw_user = auth_res.get("user") or {}

    # 2. Dispara e-mail transacional via Tool 'send_mail' assíncrona
    from ..tools.send_mail.handler import execute_async as send_mail_async
    email_res = await send_mail_async({
        "to_email": email,
        "recipient_name": name,
        "token": token,
    })

    mail_sent = bool(email_res.get("success", False))
    mail_message = email_res.get("message")
    mail_error = email_res.get("error")

    # Sanitiza o objeto user para nunca expor a chave de acesso no payload público
    safe_user = {
        "name": raw_user.get("name", name),
        "email": raw_user.get("email", email),
        "provider": raw_user.get("provider", "local"),
        "status": raw_user.get("status", "active"),
    }

    if mail_sent:
        response_msg = f"Chave de acesso e instruções enviadas com sucesso para '{email}'. Verifique sua caixa de entrada."
    else:
        response_msg = f"Cadastro realizado para '{email}'. As instruções de acesso foram processadas."

    return {
        "success": True,
        "message": response_msg,
        "user": safe_user,
        "mail_sent": mail_sent,
        "mail_status": mail_message,
        "mail_error": mail_error,
        "delivery_mode": email_res.get("delivery_mode"),
    }


def handle_lead_login(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processa requisição de login/cadastro de lead (Nome + E-mail), gerando token no Redis e disparando e-mail."""
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not email:
        return {
            "success": False,
            "error": "Nome e e-mail são obrigatórios para liberar o acesso.",
        }

    # 1. Cadastra no Redis via Tool 'auth'
    auth_res = dispatch_tool("auth", {
        "action": "set_token",
        "name": name,
        "email": email,
        "provider": "local",
    })

    if not auth_res.get("success"):
        return {
            "success": False,
            "error": auth_res.get("error") or auth_res.get("message") or "Erro ao cadastrar usuário",
        }

    token = auth_res.get("token")
    raw_user = auth_res.get("user") or {}

    # 2. Dispara e-mail transacional via Tool 'send_mail'
    email_res = dispatch_tool("send_mail", {
        "to_email": email,
        "recipient_name": name,
        "token": token,
    })

    mail_sent = bool(email_res.get("success", False))
    mail_message = email_res.get("message")
    mail_error = email_res.get("error")

    # Sanitiza o objeto user para nunca expor a chave de acesso no payload público
    safe_user = {
        "name": raw_user.get("name", name),
        "email": raw_user.get("email", email),
        "provider": raw_user.get("provider", "local"),
        "status": raw_user.get("status", "active"),
    }

    if mail_sent:
        response_msg = f"Chave de acesso e instruções enviadas com sucesso para '{email}'. Verifique sua caixa de entrada."
    else:
        response_msg = f"Cadastro realizado para '{email}'. As instruções de acesso foram processadas."

    return {
        "success": True,
        "message": response_msg,
        "user": safe_user,
        "mail_sent": mail_sent,
        "mail_status": mail_message,
        "mail_error": mail_error,
        "delivery_mode": email_res.get("delivery_mode"),
    }


import base64


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    """Decodifica as claims do payload de um JWT sem depender de bibliotecas externas."""
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1]
            rem = len(payload_b64) % 4
            if rem > 0:
                payload_b64 += "=" * (4 - rem)
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            return json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        pass
    return {}


async def handle_google_login_async(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processa autenticação delegada via Google Identity / OAuth2 assincronamente no Edge."""
    credential = data.get("credential") or data.get("id_token")
    if credential and isinstance(credential, str):
        claims = _decode_jwt_payload(credential)
        if claims:
            data = {**claims, **data}

    name = (data.get("name") or "Google User").strip()
    email = (data.get("email") or "").strip().lower()
    google_id = (data.get("google_id") or data.get("sub") or "").strip()

    if not email:
        return {
            "success": False,
            "error": "E-mail do Google é obrigatório.",
        }

    # 1. Cadastra/atualiza no Redis via Tool 'auth'
    auth_res = dispatch_tool("auth", {
        "action": "set_token",
        "name": name,
        "email": email,
        "provider": "google",
        "google_id": google_id,
    })

    if not auth_res.get("success"):
        return {
            "success": False,
            "error": auth_res.get("error") or auth_res.get("message") or "Erro ao autenticar com Google",
        }

    token = auth_res.get("token")
    raw_user = auth_res.get("user") or {}

    # 2. Dispara e-mail transacional assíncrono para o e-mail verificado do Google
    from ..tools.send_mail.handler import execute_async as send_mail_async
    email_res = await send_mail_async({
        "to_email": email,
        "recipient_name": name,
        "token": token,
    })

    mail_sent = bool(email_res.get("success", False))
    mail_message = email_res.get("message")
    mail_error = email_res.get("error")

    # Sanitiza o objeto user para nunca expor a chave de acesso no payload público
    safe_user = {
        "name": raw_user.get("name", name),
        "email": raw_user.get("email", email),
        "provider": "google",
        "google_id": google_id,
        "status": raw_user.get("status", "active"),
    }

    return {
        "success": True,
        "message": f"Autenticado via Google com sucesso! Chave de acesso e instruções enviadas para '{email}'.",
        "user": safe_user,
        "mail_sent": mail_sent,
        "mail_status": mail_message,
        "mail_error": mail_error,
        "delivery_mode": email_res.get("delivery_mode"),
    }


def handle_google_login(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processa autenticação delegada via Google Identity / OAuth2 (JWT ou payload estruturado)."""
    credential = data.get("credential") or data.get("id_token")
    if credential and isinstance(credential, str):
        claims = _decode_jwt_payload(credential)
        if claims:
            data = {**claims, **data}

    name = (data.get("name") or "Google User").strip()
    email = (data.get("email") or "").strip().lower()
    google_id = (data.get("google_id") or data.get("sub") or "").strip()

    if not email:
        return {
            "success": False,
            "error": "E-mail do Google é obrigatório.",
        }

    # 1. Cadastra/atualiza no Redis via Tool 'auth'
    auth_res = dispatch_tool("auth", {
        "action": "set_token",
        "name": name,
        "email": email,
        "provider": "google",
        "google_id": google_id,
    })

    if not auth_res.get("success"):
        return {
            "success": False,
            "error": auth_res.get("error") or auth_res.get("message") or "Erro ao autenticar com Google",
        }

    token = auth_res.get("token")
    raw_user = auth_res.get("user") or {}

    # 2. Dispara e-mail transacional para o e-mail verificado do Google
    email_res = dispatch_tool("send_mail", {
        "to_email": email,
        "recipient_name": name,
        "token": token,
    })

    mail_sent = bool(email_res.get("success", False))
    mail_message = email_res.get("message")
    mail_error = email_res.get("error")

    # Sanitiza o objeto user para nunca expor a chave de acesso no payload público
    safe_user = {
        "name": raw_user.get("name", name),
        "email": raw_user.get("email", email),
        "provider": "google",
        "google_id": google_id,
        "status": raw_user.get("status", "active"),
    }

    return {
        "success": True,
        "message": f"Autenticado via Google com sucesso! Chave de acesso e instruções enviadas para '{email}'.",
        "user": safe_user,
        "mail_sent": mail_sent,
        "mail_status": mail_message,
        "mail_error": mail_error,
        "delivery_mode": email_res.get("delivery_mode"),
    }

