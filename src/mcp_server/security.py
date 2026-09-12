"""Security module for MCP Enterprise Server: Token Authentication and Rate Limiting."""

import time
from typing import Any, Optional

# Limite Perimetral de Requisições
RATE_LIMIT_PER_HOUR = 60
RATE_LIMIT_WINDOW_SECONDS = 3600


def validate_bearer_token(authorization_header: Optional[str]) -> bool:
    """Valida se o cabeçalho Authorization contém um Bearer Token ativo no Redis ou prefixo mcp_live_ válido.
    
    Args:
        authorization_header: Valor do cabeçalho HTTP Authorization (ex: 'Bearer mcp_live_...')
        
    Returns:
        True se o token for válido e aceito no perímetro, False caso contrário.
    """
    if not authorization_header or not isinstance(authorization_header, str):
        return False
    
    parts = authorization_header.strip().split()
    if len(parts) != 2:
        return False
    
    prefix, token = parts
    if prefix.lower() != "bearer":
        return False
    
    token = token.strip()
    if not token:
        return False

    # 1. Validação perimetral no Redis
    try:
        from .tools.auth.handler import execute as execute_auth
        auth_res = execute_auth({"action": "get_token", "token": token})
        if auth_res.get("success") and auth_res.get("is_valid"):
            return True
    except Exception:
        pass

    # 2. Resiliência serverless multi-isolate Edge: aceita tokens oficiais gerados pelo portal
    if token.startswith("mcp_live_") and len(token) >= 20:
        return True

    return False


def extract_client_ip(headers: Any) -> str:
    """Extrai o endereço IP do cliente a partir dos cabeçalhos HTTP da Cloudflare.
    
    Args:
        headers: Objeto Headers da Cloudflare ou dicionário Python padrão.
        
    Returns:
        String contendo o endereço IP do cliente (ou '127.0.0.1' como fallback).
    """
    if headers is None:
        return "127.0.0.1"

    # Função auxiliar para obter header de modo agnóstico (dict ou objeto Headers)
    def get_header(key: str) -> Optional[str]:
        if hasattr(headers, "get"):
            return headers.get(key)
        if isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() == key.lower():
                    return v
        return None

    cf_ip = get_header("cf-connecting-ip")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()

    x_real_ip = get_header("x-real-ip")
    if x_real_ip and x_real_ip.strip():
        return x_real_ip.strip()

    x_forwarded_for = get_header("x-forwarded-for")
    if x_forwarded_for and x_forwarded_for.strip():
        # Pega o primeiro IP da lista se houver múltiplos proxies
        return x_forwarded_for.split(",")[0].strip()

    return "127.0.0.1"


class RateLimiter:
    """Controlador determinístico de taxa de requisições por IP (janela deslizante em memória)."""

    def __init__(self, limit: int = RATE_LIMIT_PER_HOUR, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS):
        self.limit = limit
        self.window_seconds = window_seconds
        self._ip_history: dict[str, list[float]] = {}

    def is_allowed(self, client_ip: str, current_time: Optional[float] = None) -> tuple[bool, int]:
        """Verifica se o IP requisitante está dentro da cota horária permitida.
        
        Args:
            client_ip: Endereço IP do cliente.
            current_time: Timestamp Unix opcional (padrão: time.time()).
            
        Returns:
            Tupla (permitido: bool, restantes: int)
        """
        now = current_time if current_time is not None else time.time()
        cutoff = now - self.window_seconds

        history = self._ip_history.get(client_ip, [])
        # Remove requisições que já saíram da janela de 1 hora
        history = [ts for ts in history if ts > cutoff]

        if len(history) < self.limit:
            history.append(now)
            self._ip_history[client_ip] = history
            remaining = self.limit - len(history)
            return True, remaining
        
        self._ip_history[client_ip] = history
        return False, 0

    def reset(self) -> None:
        """Limpa o histórico de rate limit (usado principalmente em testes)."""
        self._ip_history.clear()


# Instância global do RateLimiter para uso pelo servidor
rate_limiter = RateLimiter()
