"""Package initializer for deterministic tools."""

from .discover import execute_discover
from .hello import execute_hello
from .calc import execute_calc

__all__ = [
    "execute_discover",
    "execute_hello",
    "execute_calc",
]
