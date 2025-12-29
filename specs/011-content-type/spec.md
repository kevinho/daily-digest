# Feature Spec: ContentType Classification

## Overview

Add `ContentType` classification based on HTTP Content-Type headers to enable type-aware content processing. This creates a layered abstraction:

```
ItemType (routing)     → WHERE does the content come from?
ContentType (format)   → WHAT format is the content?
PlatformHandler (impl) → HOW to extract from specific platforms?
```

## User Stories

### US1: As a user, I want the system to detect content format automatically
So that different content types (HTML, PDF, images) are processed appropriately.

### US2: As a user, I want platform-specific optimizations
So that content from Twitter, YouTube, etc. is extracted with specialized handlers.

### US3: As a user, I want unsupported formats to be flagged clearly
So that I know which items cannot be processed yet.

## Functional Requirements

### FR-001: ContentType Detection
- Detect content type via HTTP HEAD request (fast, no body download)
- Map MIME types to abstract ContentType enum
- Store ContentType in Notion for visibility and filtering

### FR-002: ContentType Enum
```python
class ContentType(Enum):
    HTML = "html"           # text/html → extractable
    PDF = "pdf"             # application/pdf → future OCR
    IMAGE = "image"         # image/* → future OCR
    VIDEO = "video"         # video/* → future transcript
    AUDIO = "audio"         # audio/* → future transcript
    JSON = "json"           # application/json → API response
    TEXT = "text"           # text/plain → direct use
    BINARY = "binary"       # application/octet-stream → skip
    UNKNOWN = "unknown"     # detection failed
```

### FR-003: Platform Handler Registry
- Register handlers by domain pattern
- Each handler defines: detection, extraction, normalization
- Fallback to generic HTML handler

### FR-004: Platform Handlers (Phase 1)
| Platform | Domain Pattern | Special Handling |
|----------|---------------|------------------|
| Twitter/X | `twitter.com`, `x.com` | Smart Waiters, meta extraction |
| Generic HTML | `*` | trafilatura extraction |

### FR-005: Platform Handlers (Phase 2 - Future)
| Platform | Domain Pattern | Special Handling |
|----------|---------------|------------------|
| YouTube | `youtube.com`, `youtu.be` | Transcript API |
| GitHub | `github.com` | README extraction |
| Medium | `medium.com` | Paywall bypass |

### FR-006: ContentType Processing Matrix
| ContentType | Current Action | Future Action |
|-------------|----------------|---------------|
| HTML | Extract text | - |
| PDF | Mark unprocessed | OCR extraction |
| IMAGE | Mark unprocessed | OCR extraction |
| VIDEO | Mark unprocessed | Transcript extraction |
| AUDIO | Mark unprocessed | Transcript extraction |
| JSON | Store raw | Parse structure |
| TEXT | Direct use | - |
| BINARY | Skip | - |
| UNKNOWN | Mark error | Retry with fallback |

## Key Entities

### ContentType
- `value`: MIME-derived type string
- `processable`: boolean - can be processed now
- `future_support`: boolean - planned for future

### PlatformHandler
- `name`: Handler identifier
- `patterns`: List of domain regex patterns
- `detect()`: Check if handler applies
- `extract()`: Platform-specific extraction logic

## Edge Cases

### EC-001: Content-Type Header Missing
- Fallback: Infer from URL extension (.pdf, .jpg, etc.)
- Final fallback: Attempt HTML extraction

### EC-002: Redirect Chains
- Follow redirects up to 5 hops
- Use final URL's Content-Type

### EC-003: Content-Type Mismatch
- Some servers return wrong Content-Type
- Trust Content-Type first, validate if extraction fails

## Success Criteria

| Metric | Target |
|--------|--------|
| Detection accuracy | > 95% correct ContentType |
| HEAD request time | < 500ms average |
| Handler coverage | Twitter + Generic HTML |
| Notion field populated | 100% of URL items |

## Non-Goals (This Phase)

- PDF text extraction (OCR)
- Image text extraction (OCR)
- Video/audio transcription
- YouTube transcript API integration

