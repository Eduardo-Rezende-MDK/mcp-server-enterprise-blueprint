"""Common schemas and models for MCP Enterprise Server."""

from typing import Any, Dict, List, Optional
from .base import BaseModel, Field


class ExampleDefinition(BaseModel):
    """Represents a concrete example of tool invocation for the LLM."""

    scenario: str = Field(..., description="Descrição do cenário de uso")
    input: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros enviados na chamada")
    expectedOutput: Dict[str, Any] = Field(default_factory=dict, description="Resultado esperado")


class DocumentationDefinition(BaseModel):
    """Extended documentation and usage heuristics for the LLM."""

    summary: str = Field(..., description="Resumo funcional e objetivo da ferramenta")
    usageGuidelines: str = Field(..., description="Diretrizes para o LLM decidir quando invocar a tool")
    examples: List[ExampleDefinition] = Field(default_factory=list, description="Lista de exemplos práticos")


class ToolDefinition(BaseModel):
    """Full schema definition of an exposed MCP tool."""

    name: str = Field(..., description="Nome único identificador da ferramenta")
    description: str = Field(..., description="Descrição semântica para o LLM")
    inputSchema: Dict[str, Any] = Field(..., description="JSON Schema dos parâmetros de entrada")
    outputSchema: Dict[str, Any] = Field(..., description="JSON Schema do resultado")
    documentation: DocumentationDefinition = Field(..., description="Documentação estendida com exemplos")


class DiscoverOutput(BaseModel):
    """Output contract for the 'discover' tool."""

    total: int = Field(..., description="Quantidade total de ferramentas disponíveis")
    tools: List[ToolDefinition] = Field(..., description="Lista de ferramentas disponíveis no catálogo")
