"""
Platform-specific content handlers.

Provides a registry of handlers for extracting content from different platforms.
"""
from src.handlers.base import BaseHandler
from src.handlers.registry import get_handler, register_handler

__all__ = ["BaseHandler", "get_handler", "register_handler"]

