import asyncio
import os

import pytest

from src import dedupe
from main import process_item


def test_canonical_url_strips_tracking_and_fragment():
    url = "https://example.com/path?utm_source=newsletter&id=123#section"
    result = dedupe.canonical_url(url)
    assert "utm_source" not in result
    assert "#" not in result
    assert result.startswith("https://example.com/path")


def test_content_hash_deterministic():
    assert dedupe.content_hash("abc") == dedupe.content_hash("abc")
    assert dedupe.content_hash("abc") != dedupe.content_hash("abcd")


class FakeNotion:
    def __init__(self):
        self.status = type("S", (), {"pending": "pending", "ready": "ready"})()
        self.record = {"duplicate_of": None, "marked": [], "classified": None}

    def find_by_canonical(self, canonical_url):
        return None

    def set_duplicate_of(self, page_id, canonical_id, note):
        self.record["duplicate_of"] = (page_id, canonical_id, note)

    def set_classification(self, **kwargs):
        self.record["classified"] = kwargs

    def mark_as_done(self, page_id, summary, status=None):
        status_val = status or self.status.ready
        self.record["marked"].append(("done", page_id, summary, status_val))

    def mark_unprocessed(self, page_id, note):
        self.record["marked"].append(("unprocessed", page_id, note))

    def mark_as_error(self, page_id, note):
        self.record["marked"].append(("error", page_id, note))


def test_process_item_low_confidence(monkeypatch):
    fake = FakeNotion()
    # Force threshold to 0.5
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.5")

    async def fake_fetch(url, cdp_url):
        return "hello world"

    def fake_classify(text):
        return {"tags": ["a"], "sensitivity": "public", "confidence": 0.2, "rule_version": "r1", "prompt_version": "p1"}

    def fake_digest(text):
        return {"tldr": "short"}

    monkeypatch.setattr("main.fetch_page_content", fake_fetch)
    monkeypatch.setattr("main.classify", fake_classify)
    monkeypatch.setattr("main.generate_digest", fake_digest)

    # run process_item (it is sync but uses asyncio loop internally)
    page = {"id": "1", "url": "https://example.com/article", "attachments": []}
    process_item(page, fake, "http://localhost:9222")

    # Should mark as done with pending status due to low confidence
    assert fake.record["classified"]["confidence"] == 0.2
    assert ("done", "1", "short", fake.status.pending) in fake.record["marked"]


def test_process_item_duplicate(monkeypatch):
    fake = FakeNotion()

    existing = {"id": "abc"}

    def fake_find(canonical):
        return existing

    fake.find_by_canonical = fake_find

    page = {"id": "new", "url": "https://example.com/article", "attachments": []}
    process_item(page, fake, "http://localhost:9222")

    assert fake.record["duplicate_of"][0] == "new"
    assert fake.record["duplicate_of"][1] == "abc"


