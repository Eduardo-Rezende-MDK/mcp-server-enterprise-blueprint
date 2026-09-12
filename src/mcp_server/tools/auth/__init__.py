"""Modular package for the 'auth' MCP tool."""

from .handler import execute, generate_secure_token
from .meta import METADATA
from .schema import AuthAction, AuthInput, AuthOutput

__all__ = ["execute", "METADATA", "AuthAction", "AuthInput", "AuthOutput", "generate_secure_token"]
