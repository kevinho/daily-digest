import pytest

from main import process_item


class FakeNotion:
    def __init__(self):
        self.status = type("S", (), {"pending": "pending", "ready": "ready"})()
        self.record = {"classified": None, "marked": []}

    def find_by_canonical(self, canonical_url):
        return None

    def set_duplicate_of(self, page_id, canonical_id, note):
        raise AssertionError("Should not be called in this scenario")

    def set_classification(self, **kwargs):
        self.record["classified"] = kwargs

    def mark_as_done(self, page_id, summary, status=None):
        self.record["marked"].append(("done", page_id, summary, status))

    def mark_unprocessed(self, page_id, note):
        self.record["marked"].append(("unprocessed", page_id, note))

    def mark_as_error(self, page_id, note):
        self.record["marked"].append(("error", page_id, note))


def test_ingest_happy_path(monkeypatch):
    fake = FakeNotion()

    async def fake_fetch(url, cdp_url):
        return "hello content"

    def fake_classify(text):
        return {"tags": ["news"], "sensitivity": "public", "confidence": 0.9, "rule_version": "r1", "prompt_version": "p1"}

    def fake_digest(text):
        return {"tldr": "short summary"}

    monkeypatch.setattr("main.fetch_page_content", fake_fetch)
    monkeypatch.setattr("main.classify", fake_classify)
    monkeypatch.setattr("main.generate_digest", fake_digest)

    page = {"id": "123", "url": "https://example.com/ok", "attachments": []}
    process_item(page, fake, "http://localhost:9222")

    assert fake.record["classified"]["tags"] == ["news"]
    # Should be marked ready (default)
    assert ("done", "123", "short summary", fake.status.ready) in fake.record["marked"]


