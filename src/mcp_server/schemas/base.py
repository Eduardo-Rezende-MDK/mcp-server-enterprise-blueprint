"""Base model definition with seamless fallback for environments without Pydantic (e.g. Pyodide / Cloudflare Workers Edge)."""

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField

    BaseModel = _PydanticBaseModel
    Field = _PydanticField

except ImportError:
    from dataclasses import field
    from typing import Any, Dict

    def Field(
        default: Any = ...,
        *,
        default_factory: Any = None,
        description: str = "",
        min_length: int = None,
        **kwargs: Any,
    ) -> Any:
        """Fallback Field implementation using standard metadata."""
        if default is ... and default_factory is None:
            return field(metadata={"description": description, "min_length": min_length, **kwargs})
        elif default_factory is not None:
            return field(default_factory=default_factory, metadata={"description": description, **kwargs})
        return field(default=default, metadata={"description": description, **kwargs})

    class BaseModel:
        """Lightweight standard Python BaseModel fallback for Pyodide."""

        def __init__(self, **kwargs: Any) -> None:
            for k, v in kwargs.items():
                setattr(self, k, v)

        def model_dump(self) -> Dict[str, Any]:
            def _serialize(val: Any) -> Any:
                if hasattr(val, "model_dump"):
                    return val.model_dump()
                elif hasattr(val, "__dict__"):
                    return {k: _serialize(v) for k, v in val.__dict__.items() if not k.startswith("_")}
                elif isinstance(val, list):
                    return [_serialize(item) for item in val]
                elif isinstance(val, dict):
                    return {k: _serialize(v) for k, v in val.items()}
                return val

            return {k: _serialize(v) for k, v in self.__dict__.items() if not k.startswith("_")}
