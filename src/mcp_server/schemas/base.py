"""Base model definition with seamless fallback for environments without Pydantic (e.g. Pyodide / Cloudflare Workers Edge)."""

from typing import Any, Dict

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField

    BaseModel = _PydanticBaseModel
    Field = _PydanticField

except ImportError:
    from dataclasses import field

    def Field(
        default: Any = ...,
        *,
        default_factory: Any = None,
        description: str = "",
        min_length: int = None,
        examples: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Fallback Field implementation using standard metadata."""
        metadata = {"description": description, **kwargs}
        if min_length is not None:
            metadata["min_length"] = min_length
        if examples is not None:
            metadata["examples"] = examples

        if default is ... and default_factory is None:
            return field(metadata=metadata)
        elif default_factory is not None:
            return field(default_factory=default_factory, metadata=metadata)
        return field(default=default, metadata=metadata)

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

        @classmethod
        def model_json_schema(cls) -> Dict[str, Any]:
            properties: Dict[str, Any] = {}
            required = []
            annotations = getattr(cls, "__annotations__", {})
            for field_name, field_type in annotations.items():
                if field_name.startswith("_"):
                    continue
                prop: Dict[str, Any] = {"type": "string"}
                if field_type in (int, float):
                    prop["type"] = "number" if field_type is float else "integer"
                elif field_type is bool:
                    prop["type"] = "boolean"
                elif field_type is str:
                    prop["type"] = "string"
                elif hasattr(field_type, "__members__"):
                    prop["type"] = "string"
                    prop["enum"] = [e.value for e in field_type]
                properties[field_name] = prop
                required.append(field_name)

            return {
                "type": "object",
                "properties": properties,
                "required": required,
            }
