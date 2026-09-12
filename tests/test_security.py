"""Unit and integration tests for security module: Bearer Token Auth and Rate Limiting."""

import time
import pytest

from mcp_server.security import (
    RateLimiter,
    extract_client_ip,
    validate_bearer_token,
)
from mcp_server.registry import dispatch_tool


class TestTokenValidation:
    """Testes para a validação estrita de Bearer Token via Redis."""

    @pytest.fixture(autouse=True)
    def setup_token(self):
        """Cadastra um token de teste no Redis."""
        res = dispatch_tool("auth", {
            "action": "set_token",
            "name": "Usuario Teste",
            "email": "teste.security@empresa.com",
        })
        self.valid_token = res["token"]

    def test_bearer_token_valido(self):
        assert validate_bearer_token(f"Bearer {self.valid_token}") is True

    def test_bearer_token_case_insensitive_prefix(self):
        assert validate_bearer_token(f"bearer {self.valid_token}") is True
        assert validate_bearer_token(f"BEARER {self.valid_token}") is True

    def test_bearer_token_hardcode_rezende_rejeitado(self):
        """Garante que a antiga chave mestra hardcoded 'rezende' não existe mais e é rejeitada."""
        assert validate_bearer_token("Bearer rezende") is False

    def test_bearer_token_invalido(self):
        assert validate_bearer_token("Bearer token_invalido") is False
        assert validate_bearer_token("Bearer 123456") is False

    def test_bearer_token_sem_prefixo(self):
        assert validate_bearer_token(self.valid_token) is False
        assert validate_bearer_token(f"Basic {self.valid_token}") is False

    def test_bearer_token_nulo_ou_vazio(self):
        assert validate_bearer_token(None) is False
        assert validate_bearer_token("") is False
        assert validate_bearer_token("   ") is False

    def test_bearer_token_malformado(self):
        assert validate_bearer_token("Bearer") is False
        assert validate_bearer_token(f"Bearer {self.valid_token} extra_params") is False
        assert validate_bearer_token("Bearer   ") is False


class TestExtractClientIp:
    """Testes para extração determinística de IP do cliente a partir de headers."""

    def test_extrai_cf_connecting_ip(self):
        headers = {"cf-connecting-ip": "203.0.113.195"}
        assert extract_client_ip(headers) == "203.0.113.195"

    def test_extrai_x_real_ip(self):
        headers = {"x-real-ip": "198.51.100.10"}
        assert extract_client_ip(headers) == "198.51.100.10"

    def test_extrai_primeiro_ip_x_forwarded_for(self):
        headers = {"x-forwarded-for": "198.51.100.10, 10.0.0.1, 172.16.0.1"}
        assert extract_client_ip(headers) == "198.51.100.10"

    def test_prioridade_cf_connecting_ip_sobre_outros(self):
        headers = {
            "cf-connecting-ip": "203.0.113.1",
            "x-real-ip": "198.51.100.1",
            "x-forwarded-for": "192.0.2.1",
        }
        assert extract_client_ip(headers) == "203.0.113.1"

    def test_fallback_quando_headers_ausentes(self):
        assert extract_client_ip({}) == "127.0.0.1"
        assert extract_client_ip(None) == "127.0.0.1"


class TestRateLimiter:
    """Testes para o controlador de taxa determinístico."""

    def test_rate_limiter_permite_ate_o_limite(self):
        limiter = RateLimiter(limit=5, window_seconds=60)
        client_ip = "192.168.1.100"
        t0 = 1000.0

        for i in range(5):
            allowed, remaining = limiter.is_allowed(client_ip, current_time=t0 + i)
            assert allowed is True
            assert remaining == 5 - (i + 1)

    def test_rate_limiter_bloqueia_apos_exceder_limite(self):
        limiter = RateLimiter(limit=5, window_seconds=60)
        client_ip = "192.168.1.100"
        t0 = 1000.0

        # Faz 5 requisições permitidas
        for i in range(5):
            limiter.is_allowed(client_ip, current_time=t0 + i)

        # A 6ª requisição deve ser bloqueada
        allowed, remaining = limiter.is_allowed(client_ip, current_time=t0 + 5)
        assert allowed is False
        assert remaining == 0

    def test_rate_limiter_reseta_apos_janela(self):
        limiter = RateLimiter(limit=2, window_seconds=60)
        client_ip = "192.168.1.100"
        t0 = 1000.0

        limiter.is_allowed(client_ip, current_time=t0)
        limiter.is_allowed(client_ip, current_time=t0 + 10)

        # Bloqueado no tempo t0 + 20
        allowed, _ = limiter.is_allowed(client_ip, current_time=t0 + 20)
        assert allowed is False

        # Após expirar a janela (t0 + 65), as requisições anteriores saem do histórico
        allowed, remaining = limiter.is_allowed(client_ip, current_time=t0 + 65)
        assert allowed is True
        assert remaining >= 0

    def test_rate_limiter_isola_ips_diferentes(self):
        limiter = RateLimiter(limit=2, window_seconds=60)
        ip1 = "10.0.0.1"
        ip2 = "10.0.0.2"
        t0 = 1000.0

        # Esgota cota do ip1
        limiter.is_allowed(ip1, current_time=t0)
        limiter.is_allowed(ip1, current_time=t0 + 1)
        allowed_ip1, _ = limiter.is_allowed(ip1, current_time=t0 + 2)
        assert allowed_ip1 is False

        # ip2 continua com cota livre
        allowed_ip2, remaining_ip2 = limiter.is_allowed(ip2, current_time=t0 + 2)
        assert allowed_ip2 is True
        assert remaining_ip2 == 1


class TestRbacPermissions:
    """Testes de Controle de Acesso Baseado em Papéis (RBAC)."""

    def test_admin_role_allows_all_tools(self):
        from mcp_server.security import is_tool_allowed_for_role, ADMIN_ONLY_TOOLS, PUBLIC_TOOLS
        for tool in ADMIN_ONLY_TOOLS | PUBLIC_TOOLS:
            assert is_tool_allowed_for_role(tool, "admin") is True

    def test_lead_role_blocks_admin_tools(self):
        from mcp_server.security import is_tool_allowed_for_role, ADMIN_ONLY_TOOLS, PUBLIC_TOOLS
        for tool in ADMIN_ONLY_TOOLS:
            assert is_tool_allowed_for_role(tool, "lead") is False
        for tool in PUBLIC_TOOLS:
            assert is_tool_allowed_for_role(tool, "lead") is True

    def test_marduka_token_metadata_is_admin(self):
        from mcp_server.security import get_token_metadata, MARDUKA_ADMIN_TOKEN
        meta = get_token_metadata(f"Bearer {MARDUKA_ADMIN_TOKEN}")
        assert meta is not None
        assert meta["role"] == "admin"
        assert meta["email"] == "du.rezende@gmail.com"
