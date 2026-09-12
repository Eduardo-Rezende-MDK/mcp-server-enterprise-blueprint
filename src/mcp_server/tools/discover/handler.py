"""Deterministic handler for the 'discover' MCP tool."""

from typing import Optional
from .schema import DiscoverInput, DiscoverOutput


def execute(dados: Optional[DiscoverInput] = None) -> DiscoverOutput:
    """Retorna o catálogo completo de ferramentas ativas no servidor MCP."""
    from ...registry import get_catalog
    return get_catalog()
