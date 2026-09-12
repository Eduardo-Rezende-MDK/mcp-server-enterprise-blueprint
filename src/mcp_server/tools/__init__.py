"""Auto-discovery mechanism and modular tool registry for MCP Enterprise Server."""

import importlib
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type
from ..schemas.base import BaseModel


@dataclass
class ToolPackage:
    """Represents a fully encapsulated, discovered MCP tool module."""

    name: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    execute: Callable[[Any], Any]
    metadata: Dict[str, Any]


_DISCOVERED_TOOLS: Optional[Dict[str, ToolPackage]] = None


def discover_tools(force_reload: bool = False) -> Dict[str, ToolPackage]:
    """Escaneia as subpastas de tools e carrega dinamicamente todos os módulos válidos.

    Pastas que começam com '_' (como '_template' e '__pycache__') são ignoradas.
    """
    global _DISCOVERED_TOOLS
    if _DISCOVERED_TOOLS is not None and not force_reload:
        return _DISCOVERED_TOOLS

    tools_dir = Path(__file__).resolve().parent
    discovered: Dict[str, ToolPackage] = {}

    for item in tools_dir.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith("_") or item.name.startswith("."):
            continue

        module_name = f"{__name__}.{item.name}"
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:
            continue

        execute_fn = getattr(mod, "execute", None)
        metadata = getattr(mod, "METADATA", {})
        tool_name = metadata.get("name", item.name)
        description = metadata.get("description", getattr(execute_fn, "__doc__", "") or tool_name)

        input_model: Optional[Type[BaseModel]] = None
        output_model: Optional[Type[BaseModel]] = None

        for attr_name in dir(mod):
            attr_val = getattr(mod, attr_name)
            if inspect.isclass(attr_val) and issubclass(attr_val, BaseModel) and attr_val is not BaseModel:
                if attr_name.endswith("Input"):
                    input_model = attr_val
                elif attr_name.endswith("Output"):
                    output_model = attr_val

        if execute_fn is not None and input_model is not None and output_model is not None:
            discovered[tool_name] = ToolPackage(
                name=tool_name,
                description=description,
                input_model=input_model,
                output_model=output_model,
                execute=execute_fn,
                metadata=metadata,
            )

    _DISCOVERED_TOOLS = discovered
    return discovered


# Helpers de compatibilidade direta
def execute_hello(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["hello"].execute(*args, **kwargs)


def execute_calc(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["calc"].execute(*args, **kwargs)


def execute_discover(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["discover"].execute(*args, **kwargs)


def execute_sqlite(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["sqlite"].execute(*args, **kwargs)


def execute_redis(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["redis"].execute(*args, **kwargs)


def execute_auth(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["auth"].execute(*args, **kwargs)


def execute_send_mail(*args: Any, **kwargs: Any) -> Any:
    tools = discover_tools()
    return tools["send_mail"].execute(*args, **kwargs)


__all__ = [
    "ToolPackage",
    "discover_tools",
    "execute_hello",
    "execute_calc",
    "execute_discover",
    "execute_sqlite",
    "execute_redis",
    "execute_auth",
    "execute_send_mail",
]
