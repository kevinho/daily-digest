"""
ContentType detection based on HTTP Content-Type headers.

Provides abstract content type classification for processing routing.
Detection uses HTTP HEAD requests (fast, no body download) with extension fallback.
"""
import asyncio
import logging
from enum import Enum
from typing import Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """
    Abstract content type classification.
    
    Based on HTTP Content-Type MIME types, mapped to processing categories.
    """
    HTML = "html"           # text/html, application/xhtml+xml → extractable
    PDF = "pdf"             # application/pdf → future OCR
    IMAGE = "image"         # image/* → future OCR
    VIDEO = "video"         # video/* → future transcript
    AUDIO = "audio"         # audio/* → future transcript
    JSON = "json"           # application/json → parse structure
    TEXT = "text"           # text/plain → direct use
    BINARY = "binary"       # application/octet-stream → skip
    UNKNOWN = "unknown"     # detection failed

    @property
    def processable(self) -> bool:
        """Check if this content type can be processed (text extraction)."""
        return self in {ContentType.HTML, ContentType.TEXT, ContentType.JSON}
    
    @property
    def future_support(self) -> bool:
        """Check if this content type will be supported in the future."""
        return self in {ContentType.PDF, ContentType.IMAGE, ContentType.VIDEO, ContentType.AUDIO}


# MIME type to ContentType mapping
# For prefix matches (e.g., image/*), store with trailing slash
MIME_MAP = {
    # HTML
    "text/html": ContentType.HTML,
    "application/xhtml+xml": ContentType.HTML,
    # PDF
    "application/pdf": ContentType.PDF,
    # JSON
    "application/json": ContentType.JSON,
    "text/json": ContentType.JSON,
    # Plain text
    "text/plain": ContentType.TEXT,
    # Binary
    "application/octet-stream": ContentType.BINARY,
}

# Prefix matches for wildcard MIME types
MIME_PREFIX_MAP = {
    "image/": ContentType.IMAGE,
    "video/": ContentType.VIDEO,
    "audio/": ContentType.AUDIO,
}

# URL extension to ContentType fallback
EXTENSION_MAP = {
    # HTML
    ".html": ContentType.HTML,
    ".htm": ContentType.HTML,
    ".xhtml": ContentType.HTML,
    # PDF
    ".pdf": ContentType.PDF,
    # Images
    ".jpg": ContentType.IMAGE,
    ".jpeg": ContentType.IMAGE,
    ".png": ContentType.IMAGE,
    ".gif": ContentType.IMAGE,
    ".webp": ContentType.IMAGE,
    ".svg": ContentType.IMAGE,
    ".ico": ContentType.IMAGE,
    ".bmp": ContentType.IMAGE,
    # Video
    ".mp4": ContentType.VIDEO,
    ".webm": ContentType.VIDEO,
    ".avi": ContentType.VIDEO,
    ".mov": ContentType.VIDEO,
    ".mkv": ContentType.VIDEO,
    # Audio
    ".mp3": ContentType.AUDIO,
    ".wav": ContentType.AUDIO,
    ".ogg": ContentType.AUDIO,
    ".flac": ContentType.AUDIO,
    ".m4a": ContentType.AUDIO,
    # JSON
    ".json": ContentType.JSON,
    # Text
    ".txt": ContentType.TEXT,
    ".md": ContentType.TEXT,
    ".csv": ContentType.TEXT,
}

# Domains known to serve HTML (used as fallback when HEAD fails)
HTML_DOMAINS = {
    # Social media
    "twitter.com", "x.com", "facebook.com", "instagram.com", "linkedin.com",
    "reddit.com", "tiktok.com", "youtube.com", "youtu.be",
    # Chinese platforms
    "mp.weixin.qq.com", "weixin.qq.com", "weibo.com", "zhihu.com",
    "juejin.cn", "jianshu.com", "csdn.net", "bilibili.com",
    "xiaohongshu.com", "douyin.com", "toutiao.com",
    # News & articles
    "medium.com", "substack.com", "notion.so", "notion.site",
    "github.com", "gitlab.com", "stackoverflow.com",
    # General article sites
    "nytimes.com", "washingtonpost.com", "bbc.com", "cnn.com",
    "theguardian.com", "techcrunch.com", "arstechnica.com",
}


def parse_mime_type(content_type_header: Optional[str]) -> ContentType:
    """
    Parse Content-Type header to ContentType enum.
    
    Args:
        content_type_header: HTTP Content-Type header value (e.g., "text/html; charset=utf-8")
        
    Returns:
        ContentType enum value
    """
    if not content_type_header:
        return ContentType.UNKNOWN
    
    # Extract MIME type (before semicolon)
    mime = content_type_header.split(";")[0].strip().lower()
    
    # Exact match first
    if mime in MIME_MAP:
        return MIME_MAP[mime]
    
    # Prefix match for wildcards
    for prefix, ctype in MIME_PREFIX_MAP.items():
        if mime.startswith(prefix):
            return ctype
    
    # Handle text/* as text
    if mime.startswith("text/"):
        return ContentType.TEXT
    
    # Handle application/* that we don't recognize as binary
    if mime.startswith("application/"):
        return ContentType.BINARY
    
    return ContentType.UNKNOWN


def infer_from_extension(url: str) -> ContentType:
    """
    Infer ContentType from URL file extension.
    
    Args:
        url: URL string
        
    Returns:
        ContentType enum value, UNKNOWN if no extension match
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Get extension (including dot)
        for ext, ctype in EXTENSION_MAP.items():
            if path.endswith(ext):
                return ctype
        
        return ContentType.UNKNOWN
    except Exception:
        return ContentType.UNKNOWN


def infer_from_domain(url: str) -> ContentType:
    """
    Infer ContentType from known domain patterns.
    
    Used as fallback when HEAD request fails.
    
    Args:
        url: URL string
        
    Returns:
        ContentType.HTML if domain is known to serve HTML, UNKNOWN otherwise
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        
        # Check exact domain match
        for domain in HTML_DOMAINS:
            if hostname == domain or hostname.endswith("." + domain):
                return ContentType.HTML
        
        return ContentType.UNKNOWN
    except Exception:
        return ContentType.UNKNOWN


def _fallback_inference(url: str, reason_prefix: str) -> Tuple[ContentType, str]:
    """
    Chain of fallback inferences: extension -> domain -> unknown.
    
    Args:
        url: URL to check
        reason_prefix: Prefix for the reason string (e.g., "HEAD timeout")
        
    Returns:
        Tuple of (ContentType, reason_string)
    """
    # Try extension first
    ext_type = infer_from_extension(url)
    if ext_type != ContentType.UNKNOWN:
        return (ext_type, f"Inferred from extension ({reason_prefix})")
    
    # Try domain-based inference
    domain_type = infer_from_domain(url)
    if domain_type != ContentType.UNKNOWN:
        return (domain_type, f"Inferred from domain ({reason_prefix})")
    
    return (ContentType.UNKNOWN, reason_prefix)


async def detect_content_type(
    url: str,
    timeout: float = 5.0,
    follow_redirects: bool = True,
    max_redirects: int = 5,
) -> Tuple[ContentType, str]:
    """
    Detect ContentType via HTTP HEAD request.
    
    Uses HEAD request to avoid downloading full content.
    Falls back to URL extension, then domain inference if HEAD fails.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        max_redirects: Maximum redirect hops
        
    Returns:
        Tuple of (ContentType, reason_string)
    """
    try:
        import httpx
    except ImportError:
        return _fallback_inference(url, "httpx not installed")
    
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=follow_redirects,
            max_redirects=max_redirects,
        ) as client:
            resp = await client.head(url)
            content_type_header = resp.headers.get("content-type")
            
            if content_type_header:
                ctype = parse_mime_type(content_type_header)
                if ctype != ContentType.UNKNOWN:
                    return (ctype, f"Content-Type: {content_type_header}")
            
            # Fallback to extension
            ext_type = infer_from_extension(url)
            if ext_type != ContentType.UNKNOWN:
                return (ext_type, f"Inferred from extension (no Content-Type header)")
            
            # Fallback to domain
            domain_type = infer_from_domain(url)
            if domain_type != ContentType.UNKNOWN:
                return (domain_type, f"Inferred from domain (no Content-Type header)")
            
            # If response was successful but no type detected, assume HTML
            if resp.status_code < 400:
                return (ContentType.HTML, "Assumed HTML (successful response, no Content-Type)")
            
            return (ContentType.UNKNOWN, f"HTTP {resp.status_code}, no Content-Type")
            
    except httpx.TimeoutException:
        return _fallback_inference(url, "HEAD timeout")
        
    except Exception as e:
        return _fallback_inference(url, f"HEAD error: {e}")


def detect_content_type_sync(url: str, timeout: float = 5.0) -> Tuple[ContentType, str]:
    """Synchronous wrapper for detect_content_type."""
    return asyncio.run(detect_content_type(url, timeout))

