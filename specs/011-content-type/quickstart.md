# Quickstart: ContentType Classification

## Quick Overview

```
ItemType  → Routing     → URL_RESOURCE / NOTE_CONTENT / EMPTY_INVALID
ContentType → Format    → HTML / PDF / IMAGE / VIDEO / AUDIO / ...
Handler   → Extraction  → TwitterHandler / GenericHandler / ...
```

## New Files

```
src/content_type.py      # ContentType enum + detection
src/handlers/
├── __init__.py
├── base.py              # BaseHandler ABC
├── registry.py          # Handler registration
├── twitter.py           # Twitter extraction
└── generic.py           # Default HTML extraction
```

## Key APIs

```python
# ContentType detection
from src.content_type import detect_content_type, ContentType

content_type, reason = await detect_content_type("https://example.com/doc.pdf")
# → (ContentType.PDF, "Content-Type: application/pdf")

if content_type.processable:
    # Extract content
else:
    # Mark as unprocessed

# Handler selection
from src.handlers.registry import get_handler

handler = get_handler("https://twitter.com/user/status/123")
# → TwitterHandler instance

title, content = await handler.extract(page, url)
```

## Notion Schema Addition

New select field: `ContentType`
- Options: html, pdf, image, video, audio, json, text, binary, unknown

## Adding a New Handler

```python
# src/handlers/youtube.py
from .base import BaseHandler
from .registry import register_handler

@register_handler
class YouTubeHandler(BaseHandler):
    name = "youtube"
    patterns = [r"(youtube\.com|youtu\.be)"]
    
    async def extract(self, page, url) -> tuple[str, str]:
        # YouTube-specific extraction
        ...
```

