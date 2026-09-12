"""Schemas for the 'send_mail' MCP tool."""

from typing import Optional
from ...schemas.base import BaseModel, Field


class SendMailInput(BaseModel):
    """Parâmetros de entrada para o envio de e-mails transacionais com credenciais MCP."""

    to_email: str = Field(
        ...,
        description="Endereço de e-mail de destino do usuário cadastrado",
        examples=["eduardo@empresa.com", "dev@mcp.io"],
    )
    recipient_name: str = Field(
        ...,
        description="Nome do destinatário para personalização do e-mail",
        examples=["Eduardo Rezende", "Ana Souza"],
    )
    token: str = Field(
        ...,
        description="Bearer Token de acesso gerado para o usuário (ex: 'mcp_live_...')",
        examples=["mcp_live_e8471b045e758763118cfbf5ec94a02c"],
    )
    subject: Optional[str] = Field(
        default="Sua Chave de Acesso · MCP Server Enterprise",
        description="Assunto da mensagem de e-mail",
        examples=["Sua Chave de Acesso · MCP Server Enterprise"],
    )
    server_url: Optional[str] = Field(
        default="https://mcp-server-enterprise.mardukasoft.online",
        description="URL pública do servidor MCP para snippets de configuração",
        examples=["https://mcp-server-enterprise.mardukasoft.online"],
    )


class SendMailOutput(BaseModel):
    """Resultado estruturado do disparo de e-mail."""

    success: bool = Field(..., description="Indica se o e-mail foi disparado ou enfileirado com sucesso")
    message: str = Field(..., description="Mensagem de status do envio")
    message_id: Optional[str] = Field(default=None, description="Identificador único da mensagem (Message-ID)")
    delivery_mode: str = Field(..., description="Modo de entrega ou status: 'gmail_smtp', 'unconfigured', 'smtp_failed', 'validation_failed'")
    timestamp: str = Field(..., description="Carimbo de data e hora do envio em ISO 8601 UTC")
    error: Optional[str] = Field(default=None, description="Detalhes do erro em caso de falha no envio")
