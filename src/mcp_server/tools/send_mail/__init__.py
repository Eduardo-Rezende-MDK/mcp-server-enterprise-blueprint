"""Modular package for the 'send_mail' MCP tool."""

from .handler import execute, build_email_content
from .meta import METADATA
from .schema import SendMailInput, SendMailOutput

__all__ = ["execute", "METADATA", "SendMailInput", "SendMailOutput", "build_email_content"]
