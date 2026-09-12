"""Base model definition with seamless fallback for environments without Pydantic (e.g. Pyodide / Cloudflare Workers Edge)."""

from typing import Any, Callable, Dict, Optional

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField

    BaseModel = _PydanticBaseModel
    Field = _PydanticField

except ImportError:
    class _FieldInfo:
        """Armazena metadados e valores default para campos em ambientes sem Pydantic."""

        def __init__(
            self,
            default: Any = ...,
            default_factory: Optional[Callable[[], Any]] = None,
            description: str = "",
            min_length: Optional[int] = None,
            examples: Any = None,
            **extra: Any,
        ):
            self.default = default
            self.default_factory = default_factory
            self.description = description
            self.min_length = min_length
            self.examples = examples
            self.extra = extra

        def get_default(self) -> Any:
            if self.default is not ...:
                return self.default
            if self.default_factory is not None:
                return self.default_factory()
            return None

    def Field(
        default: Any = ...,
        *,
        default_factory: Any = None,
        description: str = "",
        min_length: int = None,
        examples: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Fallback Field implementation returning field metadata info."""
        return _FieldInfo(
            default=default,
            default_factory=default_factory,
            description=description,
            min_length=min_length,
            examples=examples,
            **kwargs,
        )

    class BaseModel:
        """Lightweight standard Python BaseModel fallback for Pyodide."""

        def __init__(self, **kwargs: Any) -> None:
            # 1. Coletar anotações de tipo e atributos padrão na árvore MRO
            annotations: Dict[str, Any] = {}
            for cls in reversed(self.__class__.__mro__):
                if cls is object:
                    continue
                annotations.update(getattr(cls, "__annotations__", {}))

                for attr, val in getattr(cls, "__dict__", {}).items():
                    if attr.startswith("_"):
                        continue
                    if isinstance(val, (classmethod, staticmethod, property)) or callable(val):
                        continue
                    if isinstance(val, _FieldInfo):
                        setattr(self, attr, val.get_default())
                    else:
                        setattr(self, attr, val)

            for attr in annotations:
                if attr.startswith("_"):
                    continue
                if not hasattr(self, attr):
                    setattr(self, attr, None)

            # 2. Atribuir os valores passados explicitamente com coerção de Enum
            for k, v in kwargs.items():
                target_type = annotations.get(k)
                if target_type and hasattr(target_type, "__members__") and v is not None:
                    try:
                        v = target_type(v)
                    except Exception:
                        pass
                setattr(self, k, v)

        def model_dump(self) -> Dict[str, Any]:
            def _serialize(val: Any) -> Any:
                if hasattr(val, "model_dump"):
                    return val.model_dump()
                elif hasattr(val, "value"):
                    return val.value
                elif hasattr(val, "__dict__"):
                    return {k: _serialize(v) for k, v in val.__dict__.items() if not k.startswith("_") and not callable(v)}
                elif isinstance(val, list):
                    return [_serialize(item) for item in val]
                elif isinstance(val, dict):
                    return {k: _serialize(v) for k, v in val.items()}
                return val

            annotations = {}
            for cls in self.__class__.__mro__:
                annotations.update(getattr(cls, "__annotations__", {}))

            allowed_keys = set(annotations.keys()) if annotations else set(self.__dict__.keys())

            return {
                k: _serialize(v)
                for k, v in self.__dict__.items()
                if not k.startswith("_") and not callable(v) and (not allowed_keys or k in allowed_keys)
            }

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

                field_val = getattr(cls, field_name, None)
                if isinstance(field_val, _FieldInfo):
                    if field_val.description:
                        prop["description"] = field_val.description
                    if field_val.examples:
                        prop["examples"] = field_val.examples
                    if field_val.default is not ...:
                        prop["default"] = field_val.default

                properties[field_name] = prop
                required.append(field_name)

            return {
                "type": "object",
                "properties": properties,
                "required": required,
            }
