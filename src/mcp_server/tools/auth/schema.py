"""Schemas for the 'auth' MCP tool."""

from enum import Enum
from typing import Any, Dict, Optional
from ...schemas.base import BaseModel, Field


class AuthAction(str, Enum):
    """Operações determinísticas de autenticação e gestão de tokens."""

    SETUP = "setup"
    TOKEN_GENERATOR = "token_generator"
    SET_TOKEN = "set_token"
    GET_TOKEN = "get_token"


class AuthInput(BaseModel):
    """Parâmetros de entrada para operações de identidade e tokens."""

    action: AuthAction = Field(
        default=AuthAction.GET_TOKEN,
        description="Ação de autenticação a executar: 'setup', 'token_generator', 'set_token' ou 'get_token'",
        examples=["set_token", "get_token", "token_generator"],
    )
    name: Optional[str] = Field(
        default=None,
        description="Nome completo do usuário (usado no cadastro em 'set_token')",
        examples=["Eduardo Rezende", "Ana Souza"],
    )
    email: Optional[str] = Field(
        default=None,
        description="Endereço de e-mail único do usuário (usado em 'set_token' e busca em 'get_token')",
        examples=["eduardo@empresa.com", "dev@mcp.io"],
    )
    token: Optional[str] = Field(
        default=None,
        description="Bearer Token de acesso com prefixo 'mcp_live_' (validado em 'get_token' ou atribuído em 'set_token')",
        examples=["mcp_live_a1b2c3d4e5f6789012345678abcdef01"],
    )
    provider: Optional[str] = Field(
        default="local",
        description="Provedor de autenticação: 'local' (form nome+email) ou 'google' (OAuth2/SSO)",
        examples=["local", "google"],
    )
    google_id: Optional[str] = Field(
        default=None,
        description="Identificador único da conta Google (usado quando provider='google')",
        examples=["109876543210987654321"],
    )


class AuthOutput(BaseModel):
    """Resultado estruturado da operação de autenticação."""

    success: bool = Field(..., description="Indica se a operação foi executada com sucesso")
    message: str = Field(..., description="Mensagem descritiva do resultado da operação")
    action: str = Field(..., description="Ação executada")
    token: Optional[str] = Field(default=None, description="Bearer Token gerado ou retornado")
    user: Optional[Dict[str, Any]] = Field(default=None, description="Dicionário com os dados cadastrais do usuário")
    is_valid: Optional[bool] = Field(default=None, description="Indica se o token consultado é válido e ativo no perímetro")
    error: Optional[str] = Field(default=None, description="Mensagem de erro detalhada em caso de falha")
