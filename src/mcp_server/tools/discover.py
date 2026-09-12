"""Deterministic implementation of the 'discover' MCP tool."""

from ..registry import get_catalog
from ..schemas.common import DiscoverOutput


def execute_discover() -> DiscoverOutput:
    """Retorna o catálogo completo de ferramentas, schemas e documentação estendida."""
    return get_catalog()
