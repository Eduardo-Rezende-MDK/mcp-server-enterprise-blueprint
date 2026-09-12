"""Deterministic implementation of the 'hello' MCP tool."""

from datetime import datetime, timezone
from ..schemas.hello import HelloInput, HelloOutput


def execute_hello(dados: HelloInput) -> HelloOutput:
    """Retorna saudação personalizada acompanhada do timestamp UTC atual."""
    agora_iso = datetime.now(timezone.utc).isoformat()
    mensagem = f"Olá, {dados.name.strip()}! Servidor MCP Enterprise operacional."
    return HelloOutput(message=mensagem, timestamp=agora_iso)
