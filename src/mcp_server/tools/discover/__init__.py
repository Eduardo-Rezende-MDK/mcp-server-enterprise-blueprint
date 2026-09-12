"""Module export for 'discover' tool."""

from .handler import execute
from .meta import METADATA
from .schema import DiscoverInput, DiscoverOutput

__all__ = ["execute", "DiscoverInput", "DiscoverOutput", "METADATA"]
