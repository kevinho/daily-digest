"""
Base class for platform-specific content handlers.
"""
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from urllib.parse import urlparse


class BaseHandler(ABC):
    """
    Abstract base class for platform-specific content handlers.
    
    Subclasses must implement:
    - name: Handler identifier
    - patterns: List of domain regex patterns
    - extract(): Platform-specific extraction logic
    """
    
    name: str = "base"
    patterns: List[str] = []
    
    @classmethod
    def matches(cls, url: str) -> bool:
        """
        Check if this handler should process the URL.
        
        Matches URL hostname against registered patterns.
        
        Args:
            url: URL to check
            
        Returns:
            True if this handler should process the URL
        """
        if not url or not cls.patterns:
            return False
        
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            
            for pattern in cls.patterns:
                if re.search(pattern, hostname, re.IGNORECASE):
                    return True
            return False
        except Exception:
            return False
    
    @abstractmethod
    async def extract(self, page, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract content from the page.
        
        Args:
            page: Playwright Page object
            url: URL being processed
            
        Returns:
            Tuple of (title, content) - either can be None if extraction fails
        """
        raise NotImplementedError
    
    async def wait_for_content(self, page) -> bool:
        """
        Wait for content to be ready on the page.
        
        Override in subclasses for custom waiting logic.
        
        Args:
            page: Playwright Page object
            
        Returns:
            True if content is ready, False if timed out
        """
        # Default: simple delay for dynamic content
        await page.wait_for_timeout(1500)
        return True
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} patterns={self.patterns}>"

