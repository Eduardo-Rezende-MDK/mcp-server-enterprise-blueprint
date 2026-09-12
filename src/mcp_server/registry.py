"""Dynamic registry and catalog manager for MCP Enterprise Server."""

from typing import Any, Dict, List
from .schemas.common import (
    DiscoverOutput,
    DocumentationDefinition,
    ToolDefinition,
)
from .tools import discover_tools


def build_tool_definitions() -> List[ToolDefinition]:
    """Gera dinamicamente a lista de definições de ferramentas a partir dos módulos descobertos."""
    packages = discover_tools()
    definitions: List[ToolDefinition] = []

    for name, pkg in packages.items():
        doc_def = pkg.metadata.get(
            "documentation",
            DocumentationDefinition(
                summary=pkg.description,
                usageGuidelines=f"Invoque a ferramenta '{name}' para executar sua operação determinística.",
                examples=[],
            ),
        )

        input_schema = pkg.input_model.model_json_schema()
        output_schema = pkg.output_model.model_json_schema()

        definitions.append(
            ToolDefinition(
                name=name,
                description=pkg.description,
                inputSchema=input_schema,
                outputSchema=output_schema,
                documentation=doc_def,
            )
        )

    return definitions


# Propriedade dinâmica para compatibilidade
class _ToolDefinitionsProxy(list):
    def __iter__(self):
        return iter(build_tool_definitions())

    def __len__(self):
        return len(build_tool_definitions())

    def __getitem__(self, index):
        return build_tool_definitions()[index]


TOOL_DEFINITIONS = _ToolDefinitionsProxy()


def get_catalog() -> DiscoverOutput:
    """Retorna o catálogo completo de ferramentas ativas gerado dinamicamente."""
    tools = build_tool_definitions()
    return DiscoverOutput(
        total=len(tools),
        tools=tools,
    )


def dispatch_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Valida os argumentos de entrada e executa deterministamente a ferramenta solicitada.

    Args:
        tool_name (str): Nome identificador da ferramenta.
        args (Dict[str, Any]): Parâmetros brutos enviados na chamada JSON-RPC.

    Returns:
        Dict[str, Any]: Dicionário serializado com o resultado da execução.

    Raises:
        KeyError: Se a ferramenta não existir no catálogo.
        ValidationError: Se os parâmetros violarem o schema Pydantic.
        ValueError: Se a lógica determinística falhar (ex: divisão por zero).
    """
    tools = discover_tools()
    pkg = tools.get(tool_name)
    if not pkg:
        raise KeyError(f"Ferramenta '{tool_name}' não encontrada.")

    # Validação e parsing via Pydantic Model da Tool
    if isinstance(args, dict):
        validated_input = pkg.input_model(**args)
    else:
        validated_input = pkg.input_model()

    # Execução determinística
    result = pkg.execute(validated_input)

    # Retorno estruturado serializado
    if hasattr(result, "model_dump"):
        return result.model_dump()
    elif isinstance(result, dict):
        return result
    return {"result": result}
