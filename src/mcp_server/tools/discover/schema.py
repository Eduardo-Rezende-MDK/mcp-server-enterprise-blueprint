"""Schemas for the 'discover' MCP tool."""

from typing import List
from ...schemas.base import BaseModel, Field
from ...schemas.common import ToolDefinition


class DiscoverInput(BaseModel):
    """Input parameters for the 'discover' tool (empty)."""

    pass


class DiscoverOutput(BaseModel):
    """Output contract for the 'discover' tool."""

    total: int = Field(..., description="Quantidade total de ferramentas disponíveis")
    tools: List[ToolDefinition] = Field(..., description="Lista completa de ferramentas disponíveis com schemas e metadados")
