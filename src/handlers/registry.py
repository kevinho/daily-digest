"""
Handler registry for platform-specific content extraction.

Handlers are matched in registration order.
GenericHandler is the fallback (should be registered last).
"""
from typing import List, Type

from src.handlers.base import BaseHandler

# Registry of handler classes (order matters - first match wins)
_HANDLERS: List[Type[BaseHandler]] = []


def register_handler(handler_cls: Type[BaseHandler]) -> Type[BaseHandler]:
    """
    Register a handler class.
    
    Can be used as a decorator:
        @register_handler
        class MyHandler(BaseHandler):
            ...
    
    Or called directly:
        register_handler(MyHandler)
    
    Args:
        handler_cls: Handler class to register
        
    Returns:
        The handler class (for decorator use)
    """
    if handler_cls not in _HANDLERS:
        _HANDLERS.append(handler_cls)
    return handler_cls


def get_handler(url: str) -> BaseHandler:
    """
    Get the appropriate handler for a URL.
    
    Returns the first handler whose patterns match the URL.
    Falls back to GenericHandler if no specific handler matches.
    
    Args:
        url: URL to find handler for
        
    Returns:
        Handler instance
    """
    for handler_cls in _HANDLERS:
        if handler_cls.matches(url):
            return handler_cls()
    
    # If no handlers registered or none match, return generic
    # Import here to avoid circular imports
    from src.handlers.generic import GenericHandler
    return GenericHandler()


def get_all_handlers() -> List[Type[BaseHandler]]:
    """Get all registered handler classes."""
    return list(_HANDLERS)


def clear_handlers() -> None:
    """Clear all registered handlers (for testing)."""
    _HANDLERS.clear()

