"""Modular package for the 'redis' MCP tool."""

from .handler import execute
from .meta import METADATA
from .schema import ConnectionInfo, RedisAction, RedisInput, RedisOutput

__all__ = ["execute", "METADATA", "RedisAction", "RedisInput", "RedisOutput", "ConnectionInfo"]
