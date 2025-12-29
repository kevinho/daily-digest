# Implementation Plan: ContentType Classification

## Technical Context

- **Language/Version**: Python 3.11
- **Key Dependencies**: 
  - `httpx` for async HEAD requests (lightweight, no full download)
  - `playwright` for browser-based extraction
  - Existing: `trafilatura`, `notion-client`
- **Target Platform**: macOS desktop runner

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Preprocessing Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────┐  │
│  │ ItemType │───▶│ ContentType   │───▶│ PlatformHandler  │  │
│  │ Routing  │    │ Detection     │    │ Registry         │  │
│  └──────────┘    └───────────────┘    └──────────────────┘  │
│       │                 │                      │             │
│       ▼                 ▼                      ▼             │
│  URL_RESOURCE     HTTP HEAD            Match domain         │
│  NOTE_CONTENT     → MIME type          → Select handler     │
│  EMPTY_INVALID    → ContentType        → Extract content    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure Changes

```
src/
├── routing.py          # Existing: ItemType
├── content_type.py     # NEW: ContentType enum + detection
├── handlers/           # NEW: Platform handlers
│   ├── __init__.py
│   ├── base.py         # BaseHandler abstract class
│   ├── registry.py     # Handler registration + dispatch
│   ├── twitter.py      # Twitter-specific logic (moved from browser.py)
│   └── generic.py      # Default HTML handler
├── browser.py          # Refactor: delegate to handlers
├── preprocess.py       # Update: integrate ContentType
└── notion.py           # Update: add ContentType property
```

## Implementation Details

### 1. ContentType Enum & Detection (`src/content_type.py`)

```python
from enum import Enum
from typing import Optional, Tuple
import httpx

class ContentType(Enum):
    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"
    UNKNOWN = "unknown"

    @property
    def processable(self) -> bool:
        return self in {ContentType.HTML, ContentType.TEXT, ContentType.JSON}

MIME_MAP = {
    "text/html": ContentType.HTML,
    "application/xhtml+xml": ContentType.HTML,
    "application/pdf": ContentType.PDF,
    "image/": ContentType.IMAGE,  # prefix match
    "video/": ContentType.VIDEO,
    "audio/": ContentType.AUDIO,
    "application/json": ContentType.JSON,
    "text/plain": ContentType.TEXT,
    "application/octet-stream": ContentType.BINARY,
}

EXTENSION_MAP = {
    ".html": ContentType.HTML,
    ".htm": ContentType.HTML,
    ".pdf": ContentType.PDF,
    ".jpg": ContentType.IMAGE,
    ".jpeg": ContentType.IMAGE,
    ".png": ContentType.IMAGE,
    ".gif": ContentType.IMAGE,
    ".webp": ContentType.IMAGE,
    ".mp4": ContentType.VIDEO,
    ".webm": ContentType.VIDEO,
    ".mp3": ContentType.AUDIO,
    ".wav": ContentType.AUDIO,
    ".json": ContentType.JSON,
    ".txt": ContentType.TEXT,
}

async def detect_content_type(url: str, timeout: float = 5.0) -> Tuple[ContentType, str]:
    """
    Detect ContentType via HTTP HEAD request.
    
    Returns:
        Tuple of (ContentType, reason_string)
    """
    ...
```

### 2. Platform Handler Base (`src/handlers/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from playwright.async_api import Page

class BaseHandler(ABC):
    """Abstract base class for platform-specific content handlers."""
    
    name: str = "base"
    patterns: list[str] = []  # Domain patterns (regex)
    
    @classmethod
    def matches(cls, url: str) -> bool:
        """Check if this handler should process the URL."""
        ...
    
    @abstractmethod
    async def extract(self, page: Page, url: str) -> Tuple[str, str]:
        """
        Extract content from the page.
        
        Returns:
            Tuple of (title, content)
        """
        ...
```

### 3. Handler Registry (`src/handlers/registry.py`)

```python
from typing import Type, Optional
from .base import BaseHandler
from .twitter import TwitterHandler
from .generic import GenericHandler

_HANDLERS: list[Type[BaseHandler]] = []

def register_handler(handler_cls: Type[BaseHandler]) -> Type[BaseHandler]:
    """Decorator to register a handler."""
    _HANDLERS.append(handler_cls)
    return handler_cls

def get_handler(url: str) -> BaseHandler:
    """Get the appropriate handler for a URL."""
    for handler_cls in _HANDLERS:
        if handler_cls.matches(url):
            return handler_cls()
    return GenericHandler()

# Auto-register handlers
register_handler(TwitterHandler)
register_handler(GenericHandler)  # Fallback last
```

### 4. Twitter Handler (`src/handlers/twitter.py`)

Move existing Twitter logic from `browser.py`:
- Smart Waiters
- Meta extraction
- DOM-based fallback

```python
@register_handler
class TwitterHandler(BaseHandler):
    name = "twitter"
    patterns = [r"(twitter\.com|x\.com)"]
    
    async def extract(self, page: Page, url: str) -> Tuple[str, str]:
        """Twitter-specific extraction with Smart Waiters."""
        ...
```

### 5. Notion Schema Update

Add `ContentType` select field:
- Options: html, pdf, image, video, audio, json, text, binary, unknown

### 6. Integration Points

**preprocess.py changes:**
```python
def _process_url_resource(page, notion, cdp_url):
    # Existing ItemType logic
    notion.set_item_type(page_id, "url_resource")
    
    # NEW: Detect ContentType
    content_type, reason = await detect_content_type(url)
    notion.set_content_type(page_id, content_type.value)
    
    if not content_type.processable:
        notion.mark_unprocessed(page_id, f"ContentType {content_type.value} not supported yet")
        return {"action": "unprocessed", "content_type": content_type.value}
    
    # Get handler and extract
    handler = get_handler(url)
    title, content = await handler.extract(page, url)
    ...
```

## Migration Notes

1. **Backward Compatibility**: Existing items without ContentType are treated as UNKNOWN
2. **Notion Schema**: Add ContentType field via `notion_align_schema.py`
3. **No Breaking Changes**: This is additive - existing flow remains functional

## Testing Strategy

```
tests/
├── test_content_type.py    # ContentType detection
├── test_handlers/
│   ├── test_registry.py    # Handler matching
│   ├── test_twitter.py     # Twitter extraction
│   └── test_generic.py     # Generic HTML extraction
└── test_preprocess.py      # Update existing tests
```

## Rollout Plan

1. **Phase 1** (This PR):
   - ContentType enum + detection
   - Handler registry + base class
   - Twitter handler (refactor from browser.py)
   - Generic handler
   - Notion ContentType field

2. **Phase 2** (Future):
   - YouTube handler (transcript API)
   - GitHub handler
   - Medium handler

3. **Phase 3** (Future):
   - PDF OCR support
   - Image OCR support
   - Video transcription

