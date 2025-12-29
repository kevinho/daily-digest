import pytest

from src import preprocess


class StubNotion:
    def __init__(self) -> None:
        self.titles = {}
        self.errors = {}

    def set_title(self, page_id: str, title: str, note: str = "") -> None:
        self.titles[page_id] = {"title": title, "note": note}

    def mark_as_error(self, page_id: str, error: str) -> None:
        self.errors[page_id] = error


def test_backfill_from_url(monkeypatch):
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Title from page\nBody")

    page = {"id": "1", "title": "", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "http://localhost:9222")
    assert result["action"] == "backfilled"
    assert notion.titles["1"]["title"].startswith("Title from page")


def test_backfill_from_content_when_url_empty(monkeypatch):
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "")
    page = {"id": "2", "title": "", "url": None, "attachments": [], "raw_content": "My content heading\nmore"}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["2"]["title"] == "My content heading"


def test_error_when_name_present_but_no_url_or_content():
    notion = StubNotion()
    page = {"id": "3", "title": "Has name", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "error"
    assert "missing URL" in notion.errors["3"]


def test_skip_when_already_valid():
    notion = StubNotion()
    page = {"id": "4", "title": "Has name", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "skip"
    assert notion.titles == {}
    assert notion.errors == {}


def test_batch_counts(monkeypatch):
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Title")
    pages = [
        {"id": "a", "title": "", "url": "http://1", "attachments": [], "raw_content": ""},
        {"id": "b", "title": "ok", "url": "http://2", "attachments": [], "raw_content": ""},
        {"id": "c", "title": "ok", "url": None, "attachments": [], "raw_content": ""},
    ]
    stats = preprocess.preprocess_batch(pages, notion, "cdp")
    assert stats["backfilled"] == 1
    assert stats["error"] == 1
    assert stats["skip"] == 1

