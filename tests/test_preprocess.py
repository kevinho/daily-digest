"""Tests for preprocessing with smart routing."""
import pytest

from src import preprocess
from src.routing import ItemType


class MockStatus:
    ready = "ready"
    error = "Error"


class StubNotion:
    """Stub NotionManager for testing."""
    
    def __init__(self) -> None:
        self.titles = {}
        self.errors = {}
        self.done = {}
        self.status = MockStatus()
        self._has_blocks = False  # Default: no content blocks

    def set_title(self, page_id: str, title: str, note: str = "") -> None:
        self.titles[page_id] = {"title": title, "note": note}

    def mark_as_error(self, page_id: str, error: str) -> None:
        self.errors[page_id] = error

    def mark_as_done(self, page_id: str, summary: str, status: str = None) -> None:
        self.done[page_id] = {"summary": summary, "status": status}

    def has_page_blocks(self, page_id: str) -> bool:
        """Return configurable result for content block check."""
        return self._has_blocks


# ============================================================
# URL_RESOURCE Tests (has URL -> backfill title from URL)
# ============================================================

def test_url_resource_backfill_from_page_title(monkeypatch):
    """URL_RESOURCE: backfill title from page title."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: "Title from page title")
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Body text")

    page = {"id": "1", "title": "", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "http://localhost:9222")
    
    assert result["action"] == "backfilled"
    assert result["item_type"] == "url_resource"
    assert notion.titles["1"]["title"] == "Title from page title"


def test_url_resource_backfill_from_content_when_title_fails(monkeypatch):
    """URL_RESOURCE: fall back to content when page title fails."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Content heading\nMore text")

    page = {"id": "2", "title": "", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "backfilled"
    assert result["item_type"] == "url_resource"
    assert notion.titles["2"]["title"] == "Content heading"


def test_url_resource_skip_when_already_valid(monkeypatch):
    """URL_RESOURCE: skip if already has meaningful name."""
    notion = StubNotion()
    page = {"id": "3", "title": "Has name", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "skip"
    assert result["item_type"] == "url_resource"
    assert notion.titles == {}


def test_url_resource_bookmark_fallback(monkeypatch):
    """URL_RESOURCE: use Bookmark:domain when all else fails."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "")
    
    page = {"id": "4", "title": "", "url": "https://example.com/page", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "backfilled"
    assert notion.titles["4"]["title"].startswith("Bookmark:example.com")


def test_url_resource_domain_placeholder_triggers_backfill(monkeypatch):
    """URL_RESOURCE: domain-like title should be backfilled."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "")
    
    page = {"id": "d", "title": "https://example.com", "url": "https://example.com/post", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "backfilled"
    assert notion.titles["d"]["title"].startswith("Bookmark:example.com")


# ============================================================
# NOTE_CONTENT Tests (no URL, has content blocks -> mark ready)
# ============================================================

def test_note_content_generates_name_and_marks_ready():
    """NOTE_CONTENT: generate NOTE-YYYYMMDD-N name and mark ready."""
    notion = StubNotion()
    notion._has_blocks = True  # Has content blocks
    
    page = {"id": "n1", "title": "", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp", note_sequence=1)
    
    assert result["action"] == "ready"
    assert result["item_type"] == "note_content"
    assert "NOTE-" in result.get("title", "")
    assert notion.done["n1"]["status"] == "ready"


def test_note_content_increments_sequence():
    """NOTE_CONTENT: sequence should be reflected in name."""
    notion = StubNotion()
    notion._has_blocks = True
    
    page = {"id": "n2", "title": "", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp", note_sequence=5)
    
    assert result["title"].endswith("-5")


def test_note_content_keeps_existing_name():
    """NOTE_CONTENT: if already has meaningful name, just mark ready."""
    notion = StubNotion()
    notion._has_blocks = True
    
    page = {"id": "n3", "title": "My Note", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "ready"
    assert "title" not in result  # Title not changed
    assert notion.done["n3"]["status"] == "ready"


def test_note_content_with_empty_url():
    """NOTE_CONTENT: empty string URL should still be NOTE_CONTENT."""
    notion = StubNotion()
    notion._has_blocks = True
    
    page = {"id": "n4", "title": "", "url": "", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "ready"
    assert result["item_type"] == "note_content"


# ============================================================
# EMPTY_INVALID Tests (no URL, no content -> Error)
# ============================================================

def test_empty_invalid_marks_error():
    """EMPTY_INVALID: no URL and no content should mark as Error."""
    notion = StubNotion()
    notion._has_blocks = False  # No content blocks
    
    page = {"id": "e1", "title": "", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "error"
    assert result["item_type"] == "empty_invalid"
    assert "e1" in notion.errors
    assert "no url" in notion.errors["e1"].lower() or "no content" in notion.errors["e1"].lower()


def test_empty_invalid_with_name_still_marks_error():
    """EMPTY_INVALID: even with name, no URL/content should mark Error."""
    notion = StubNotion()
    notion._has_blocks = False
    
    page = {"id": "e2", "title": "Has name", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "error"
    assert result["item_type"] == "empty_invalid"


# ============================================================
# Batch Processing Tests
# ============================================================

def test_batch_counts_all_types(monkeypatch):
    """Batch processing should count all action types."""
    notion = StubNotion()
    notion._has_blocks = True  # For note content items
    
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Title")
    
    pages = [
        # URL_RESOURCE: needs backfill
        {"id": "a", "title": "", "url": "http://1", "attachments": [], "raw_content": ""},
        # URL_RESOURCE: skip (already has name)
        {"id": "b", "title": "ok", "url": "http://2", "attachments": [], "raw_content": ""},
    ]
    stats = preprocess.preprocess_batch(pages, notion, "cdp")
    
    assert stats["backfilled"] == 1
    assert stats["skip"] == 1


def test_batch_increments_note_sequence():
    """Batch processing should increment sequence for NOTE_CONTENT items."""
    notion = StubNotion()
    notion._has_blocks = True
    
    pages = [
        {"id": "n1", "title": "", "url": None, "attachments": [], "raw_content": ""},
        {"id": "n2", "title": "", "url": None, "attachments": [], "raw_content": ""},
        {"id": "n3", "title": "", "url": None, "attachments": [], "raw_content": ""},
    ]
    stats = preprocess.preprocess_batch(pages, notion, "cdp")
    
    assert stats["ready"] == 3
    # Check sequential names
    assert notion.titles["n1"]["title"].endswith("-1")
    assert notion.titles["n2"]["title"].endswith("-2")
    assert notion.titles["n3"]["title"].endswith("-3")


# ============================================================
# Edge Cases
# ============================================================

def test_attachment_fallback_for_url_resource(monkeypatch):
    """URL_RESOURCE: use attachment filename when title fails."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "")
    
    page = {"id": "a1", "title": "", "url": "http://example.com", "attachments": ["https://files/doc.pdf"], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "backfilled"
    assert notion.titles["a1"]["title"] == "doc.pdf"


def test_raw_content_fallback_for_url_resource(monkeypatch):
    """URL_RESOURCE: use raw_content when URL fetch fails."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "")
    
    page = {"id": "r1", "title": "", "url": "http://example.com", "attachments": [], "raw_content": "My saved content\nMore text"}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "backfilled"
    assert notion.titles["r1"]["title"] == "My saved content"


def test_title_prefers_page_title_over_fallbacks(monkeypatch):
    """URL_RESOURCE: page title should take precedence."""
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: "Preferred Title")
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Fallback text")
    
    page = {"id": "f1", "title": "", "url": "http://example.com", "attachments": [], "raw_content": "Content"}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert notion.titles["f1"]["title"] == "Preferred Title"


def test_tweet_title_processing(monkeypatch):
    """URL_RESOURCE: Twitter URLs should process normally."""
    notion = StubNotion()
    tweet_url = "https://x.com/user/status/123456789"
    title = 'User on X: "Tweet content" / X'
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: title)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Tweet content")
    
    page = {"id": "t1", "title": "", "url": tweet_url, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    
    assert result["action"] == "backfilled"
    assert result["item_type"] == "url_resource"
    assert notion.titles["t1"]["title"] == title
