# Tasks: ContentType Classification

## US1: ContentType Detection

### T001: Create ContentType enum ✅
- [x] Create `src/content_type.py`
- [x] Define `ContentType` enum with values: HTML, PDF, IMAGE, VIDEO, AUDIO, JSON, TEXT, BINARY, UNKNOWN
- [x] Add `processable` property
- [x] Define MIME_MAP for Content-Type header mapping
- [x] Define EXTENSION_MAP for URL extension fallback

### T002: Implement HTTP HEAD detection ✅
- [x] Add `httpx` to requirements.txt
- [x] Implement `detect_content_type(url)` async function
- [x] Handle timeout gracefully (default 5s)
- [x] Follow redirects (max 5 hops)
- [x] Return `(ContentType, reason)` tuple

### T003: Implement extension-based fallback ✅
- [x] Parse URL path for extension
- [x] Map extension to ContentType via EXTENSION_MAP
- [x] Use as fallback when HEAD fails or returns generic MIME

### T004: Add ContentType unit tests ✅
- [x] Test MIME parsing for all types
- [x] Test extension fallback
- [x] Test case insensitivity
- [x] Test empty/unknown inputs

---

## US2: Platform Handler Framework

### T005: Create handler base class ✅
- [x] Create `src/handlers/` directory
- [x] Create `src/handlers/__init__.py`
- [x] Create `src/handlers/base.py` with `BaseHandler` ABC
- [x] Define abstract `extract(page, url)` method
- [x] Implement `matches(url)` class method

### T006: Create handler registry ✅
- [x] Create `src/handlers/registry.py`
- [x] Implement `register_handler` decorator
- [x] Implement `get_handler(url)` function
- [x] Ensure fallback to generic handler

### T007: Implement Generic HTML handler ✅
- [x] Create `src/handlers/generic.py`
- [x] Implement trafilatura extraction
- [x] Implement `extract()` with title and content extraction
- [x] Register as fallback handler

### T008: Implement Twitter handler ✅
- [x] Create `src/handlers/twitter.py`
- [x] Implement Smart Waiters logic
- [x] Implement meta extraction logic
- [x] Implement DOM-based fallback
- [x] Register with domain patterns: `twitter.com`, `x.com`

### T009: Add handler unit tests ✅
- [x] Test registry matching priority
- [x] Test Twitter handler detection
- [x] Test Generic handler fallback
- [x] Test extract_tweet_id utility

---

## US3: Integration & Notion Schema

### T010: Add ContentType to Notion schema ✅
- [x] Add `content_type: str = "ContentType"` to PropertyNames
- [x] Add env var `NOTION_PROP_CONTENT_TYPE` support
- [x] Add `set_content_type()` method to NotionManager
- [x] Update `_simplify_page()` to extract content_type

### T011: Integrate ContentType into preprocessing ✅
- [x] Update `_process_url_resource()` in preprocess.py
- [x] Call `detect_content_type_sync()` before extraction
- [x] Set ContentType in Notion
- [x] Skip extraction for non-processable types
- [x] Mark as unprocessed with clear reason

### T012: Refactor browser.py ⏸️ (Deferred)
- [ ] Remove Twitter-specific code (moved to handler)
- [ ] Simplify `fetch_page_content()` to use handlers
- Note: Keeping existing browser.py for now, handlers are parallel implementation

### T013: Update preprocessing tests ✅
- [x] Add ContentType detection mocks (autouse fixture)
- [x] Test processable content flow
- [x] Test non-processable content (PDF, IMAGE)
- [x] Test ContentType field setting

---

## Verification

### T014: End-to-end testing ✅
- [x] Test Twitter URL → TwitterHandler match
- [x] Test generic URL → GenericHandler fallback
- [x] Test PDF URL → ContentType.PDF → unprocessed
- [x] All 144 tests passing

### T015: Documentation update ⏸️ (Deferred)
- [ ] Update README with ContentType info
- [ ] Document handler extension pattern
- [ ] Add examples for adding new handlers

---

## Summary

| Task | Status |
|------|--------|
| T001: ContentType enum | ✅ |
| T002: HTTP HEAD detection | ✅ |
| T003: Extension fallback | ✅ |
| T004: ContentType tests | ✅ |
| T005: Handler base class | ✅ |
| T006: Handler registry | ✅ |
| T007: Generic handler | ✅ |
| T008: Twitter handler | ✅ |
| T009: Handler tests | ✅ |
| T010: Notion schema | ✅ |
| T011: Preprocessing integration | ✅ |
| T012: browser.py refactor | ⏸️ Deferred |
| T013: Preprocessing tests | ✅ |
| T014: E2E testing | ✅ |
| T015: Documentation | ⏸️ Deferred |

**Total: 13/15 completed, 2 deferred**
