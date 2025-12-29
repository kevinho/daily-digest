import types

import pytest

import main


class StubNotion:
    def __init__(self) -> None:
        self.errors = {}
        self.unprocessed = {}
        self.classifications = {}
        self.done = {}
        self.duplicates = {}

        class Status:
            ready = "ready"
            pending = "pending"
            excluded = "excluded"
            error = "Error"
            unprocessed = "unprocessed"

        self.status = Status()

    def find_by_canonical(self, canonical_url):
        return None

    def set_duplicate_of(self, page_id, canonical_id, note):
        self.duplicates[page_id] = canonical_id

    def mark_unprocessed(self, page_id, note):
        self.unprocessed[page_id] = note

    def mark_as_error(self, page_id, error):
        self.errors[page_id] = error

    def set_classification(
        self,
        page_id,
        tags,
        sensitivity,
        confidence,
        rule_version,
        prompt_version,
        raw_content=None,
        canonical_url=None,
    ):
        self.classifications[page_id] = {
            "tags": tags,
            "sensitivity": sensitivity,
            "confidence": confidence,
            "rule_version": rule_version,
            "prompt_version": prompt_version,
            "raw_content": raw_content,
            "canonical_url": canonical_url,
        }

    def mark_as_done(self, page_id, summary, status=None):
        self.done[page_id] = {"summary": summary, "status": status or self.status.ready}


@pytest.fixture(autouse=True)
def patch_dedupe(monkeypatch):
    monkeypatch.setattr("src.dedupe.canonical_url", lambda u: u)


def test_twitter_success(monkeypatch):
    notion = StubNotion()

    async def _ok(url, cdp_url):
        return "Hello tweet"

    monkeypatch.setattr("main.fetch_page_content", _ok)
    monkeypatch.setattr(
        "main.classify",
        lambda text: {
            "tags": ["twitter"],
            "sensitivity": "public",
            "confidence": 0.9,
            "rule_version": "r",
            "prompt_version": "p",
        },
    )
    monkeypatch.setattr("main.generate_digest", lambda text: {"tldr": "TLDR", "insights": ""})

    page = {"id": "1", "url": "https://x.com/user/status/123", "attachments": []}
    main.process_item(page, notion, "http://localhost:9222")

    assert notion.errors == {}
    assert notion.classifications["1"]["raw_content"] == "Hello tweet"
    assert notion.done["1"]["status"] == notion.status.ready


def test_twitter_blocked(monkeypatch):
    notion = StubNotion()

    async def blocked(url, cdp_url):
        raise RuntimeError("blocked: login/JS wall detected")

    monkeypatch.setattr("main.fetch_page_content", blocked)
    page = {"id": "2", "url": "https://twitter.com/user/status/456", "attachments": []}
    main.process_item(page, notion, "http://localhost:9222")

    assert "blocked" in notion.errors["2"]


def test_invalid_tweet_url(monkeypatch):
    notion = StubNotion()
    page = {"id": "3", "url": "https://x.com/user/invalid", "attachments": []}
    main.process_item(page, notion, "http://localhost:9222")
    assert "invalid tweet url" in notion.errors["3"]

