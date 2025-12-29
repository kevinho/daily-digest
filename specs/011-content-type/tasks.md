# Tasks: ContentType Classification

## US1: ContentType Detection

### T001: Create ContentType enum
- [ ] Create `src/content_type.py`
- [ ] Define `ContentType` enum with values: HTML, PDF, IMAGE, VIDEO, AUDIO, JSON, TEXT, BINARY, UNKNOWN
- [ ] Add `processable` property
- [ ] Define MIME_MAP for Content-Type header mapping
- [ ] Define EXTENSION_MAP for URL extension fallback

### T002: Implement HTTP HEAD detection
- [ ] Add `httpx` to requirements.txt
- [ ] Implement `detect_content_type(url)` async function
- [ ] Handle timeout gracefully (default 5s)
- [ ] Follow redirects (max 5 hops)
- [ ] Return `(ContentType, reason)` tuple

### T003: Implement extension-based fallback
- [ ] Parse URL path for extension
- [ ] Map extension to ContentType via EXTENSION_MAP
- [ ] Use as fallback when HEAD fails or returns generic MIME

### T004: Add ContentType unit tests
- [ ] Test MIME parsing for all types
- [ ] Test extension fallback
- [ ] Test redirect following
- [ ] Test timeout handling

---

## US2: Platform Handler Framework

### T005: Create handler base class
- [ ] Create `src/handlers/` directory
- [ ] Create `src/handlers/__init__.py`
- [ ] Create `src/handlers/base.py` with `BaseHandler` ABC
- [ ] Define abstract `extract(page, url)` method
- [ ] Implement `matches(url)` class method

### T006: Create handler registry
- [ ] Create `src/handlers/registry.py`
- [ ] Implement `register_handler` decorator
- [ ] Implement `get_handler(url)` function
- [ ] Ensure fallback to generic handler

### T007: Implement Generic HTML handler
- [ ] Create `src/handlers/generic.py`
- [ ] Move trafilatura extraction logic
- [ ] Implement `extract()` with existing browser logic
- [ ] Register as fallback handler

### T008: Implement Twitter handler
- [ ] Create `src/handlers/twitter.py`
- [ ] Move Smart Waiters logic from `browser.py`
- [ ] Move meta extraction logic
- [ ] Move DOM-based fallback
- [ ] Register with domain patterns: `twitter.com`, `x.com`

### T009: Add handler unit tests
- [ ] Test registry matching priority
- [ ] Test Twitter handler detection
- [ ] Test Generic handler fallback
- [ ] Test extraction interface

---

## US3: Integration & Notion Schema

### T010: Add ContentType to Notion schema
- [ ] Add `content_type: str = "ContentType"` to PropertyNames
- [ ] Update `notion_align_schema.py` for ContentType select field
- [ ] Add `set_content_type()` method to NotionManager
- [ ] Update `_simplify_page()` to extract content_type

### T011: Integrate ContentType into preprocessing
- [ ] Update `_process_url_resource()` in preprocess.py
- [ ] Call `detect_content_type()` before extraction
- [ ] Set ContentType in Notion
- [ ] Skip extraction for non-processable types
- [ ] Mark as unprocessed with clear reason

### T012: Refactor browser.py
- [ ] Remove Twitter-specific code (moved to handler)
- [ ] Simplify `fetch_page_content()` to use handlers
- [ ] Keep CDP connection management
- [ ] Keep page caching logic

### T013: Update preprocessing tests
- [ ] Add ContentType detection mocks
- [ ] Test processable content flow
- [ ] Test non-processable content (PDF, IMAGE)
- [ ] Test handler selection

---

## Verification

### T014: End-to-end testing
- [ ] Test Twitter URL → TwitterHandler → ContentType.HTML
- [ ] Test generic article → GenericHandler → ContentType.HTML
- [ ] Test PDF URL → detect → ContentType.PDF → unprocessed
- [ ] Verify ContentType field populated in Notion

### T015: Documentation update
- [ ] Update README with ContentType info
- [ ] Document handler extension pattern
- [ ] Add examples for adding new handlers

---

## Task Dependencies

```
T001 ─┬─▶ T002 ─▶ T003 ─▶ T004
      │
      └─▶ T010 ─▶ T011
          
T005 ─▶ T006 ─┬─▶ T007 ─▶ T012
              │
              └─▶ T008
              
T011 + T012 ─▶ T013 ─▶ T014 ─▶ T015
```

## MVP Checkpoint

After T011:
- ContentType detection working
- Notion field populated
- Non-processable items marked correctly

After T014:
- Full handler framework operational
- Twitter handler extracted and working
- All existing tests passing

