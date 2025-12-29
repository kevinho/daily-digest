import json
import types

import pytest

import main
from src.content_type import ContentType


class StubNotion:
    def __init__(self) -> None:
        self.errors = {}
        self.unprocessed = {}
        self.classifications = {}
        self.done = {}
        self.duplicates = {}
        self.props = {}
        self.titles = {}
        self.item_types = {}
        self.content_types = {}
        self._find_return = None
        self._has_blocks = False

        class Status:
            ready = "ready"
            pending = "pending"
            excluded = "excluded"
            error = "Error"
            unprocessed = "unprocessed"

        self.status = Status()

    def set_title(self, page_id: str, title: str, note: str = ""):
        self.titles[page_id] = {"title": title, "note": note}

    def find_by_canonical(self, canonical_url):
        return self._find_return

    def set_duplicate_of(self, page_id, canonical_id, note):
        self.duplicates[page_id] = canonical_id

    def mark_unprocessed(self, page_id, note):
        self.unprocessed[page_id] = note

    def mark_as_error(self, page_id, error):
        self.errors[page_id] = error

    def set_item_type(self, page_id: str, item_type: str) -> None:
        self.item_types[page_id] = item_type

    def set_content_type(self, page_id: str, content_type: str) -> None:
        self.content_types[page_id] = content_type

    def has_page_blocks(self, page_id: str) -> bool:
        return self._has_blocks

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
        source=None,
    ):
        self.classifications[page_id] = {
            "tags": tags,
            "sensitivity": sensitivity,
            "confidence": confidence,
            "rule_version": rule_version,
            "prompt_version": prompt_version,
            "raw_content": raw_content,
            "canonical_url": canonical_url,
            "source": source,
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
    assert notion.classifications["1"]["source"] == "manual"
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


def test_duplicate_ready_skips(monkeypatch):
    notion = StubNotion()
    notion._find_return = {"id": "ready1", "status": notion.status.ready}
    page = {"id": "4", "url": "https://x.com/user/status/999", "attachments": []}
    res = main.process_item(page, notion, "http://localhost:9222")
    assert notion.duplicates["4"] == "ready1"
    assert res == "duplicate"
    assert "4" not in notion.classifications


def test_retry_after_block(monkeypatch):
    notion = StubNotion()

    async def blocked(url, cdp_url):
        raise RuntimeError("blocked: wall")

    async def ok(url, cdp_url):
        return "hi"

    monkeypatch.setattr("main.fetch_page_content", blocked)
    page = {"id": "5", "url": "https://x.com/user/status/100", "attachments": []}
    res_block = main.process_item(page, notion, "http://localhost:9222")
    assert "blocked" in notion.errors["5"]
    assert res_block == "error"

    monkeypatch.setattr("main.fetch_page_content", ok)
    monkeypatch.setattr(
        "main.classify",
        lambda text: {
            "tags": ["twitter"],
            "sensitivity": "public",
            "confidence": 0.8,
            "rule_version": "r",
            "prompt_version": "p",
        },
    )
    monkeypatch.setattr("main.generate_digest", lambda text: {"tldr": "ok", "insights": ""})
    res_ok = main.process_item(page, notion, "http://localhost:9222")
    assert res_ok == "success"
    assert notion.classifications["5"]["raw_content"] == "hi"


def test_plugin_source(monkeypatch):
    notion = StubNotion()

    async def _ok(url, cdp_url):
        return "Plugin tweet"

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
    page = {"id": "6", "url": "https://x.com/user/status/777", "attachments": [], "source": "plugin"}
    res = main.process_item(page, notion, "http://localhost:9222")
    assert res == "success"
    assert notion.classifications["6"]["source"] == "plugin"
    assert notion.done["6"]["status"] == notion.status.ready


def test_twitter_end_to_end_title_and_body(monkeypatch):
    """End-to-end: preprocess fills title, process stores body."""
    # Arrange stubs
    notion = StubNotion()
    tweet_url = "https://x.com/demishassabis/status/2005358760047562802?s=12&t=kmKQtU-_oyvUW6FjhHSNTw"
    page = {"id": "7", "title": "", "url": tweet_url, "attachments": [], "raw_content": ""}
    expected_title = (
        'Demis Hassabis on X: "Amazing work from the incredibly talented Director Greg Kohs, '
        "Producers Gary Kreig & Jonathan Fildes, and a wonderful score from the maestro Dan Deacon - enjoy! "
        'https://t.co/fagdivZ9qN" / X'
    )
    body = (
        "Amazing work from the incredibly talented Director Greg Kohs, Producers Gary Kreig & Jonathan Fildes, "
        "and a wonderful score from the maestro Dan Deacon - enjoy!"
    )

    # Preprocess: mock title/text fetch and content type detection
    from src import preprocess

    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: expected_title)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: body)
    monkeypatch.setattr(preprocess, "detect_content_type_sync", lambda url, timeout=5.0: (ContentType.HTML, "mocked"))
    res = preprocess.preprocess_item(page, notion, "cdp")
    assert res["action"] == "backfilled"
    assert notion.titles["7"]["title"] == expected_title

    # Process: mock content fetch/classify/summarize
    async def _body(url, cdp_url):
        return body

    monkeypatch.setattr("main.fetch_page_content", _body)
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
    monkeypatch.setattr("main.generate_digest", lambda text: {"tldr": "tldr", "insights": ""})
    result = main.process_item(page, notion, "http://localhost:9222")

    print(json.dumps(notion.titles, indent=2))
    assert result == "success"
    assert notion.classifications["7"]["raw_content"] == body
    assert notion.done["7"]["status"] == notion.status.ready
    assert notion.done["7"]["summary"].startswith("tldr")


def test_twitter_end_to_end_title_and_body_deepseek(monkeypatch):
    """End-to-end for akshay_pachaar tweet with rich title/body."""
    notion = StubNotion()
    tweet_url = "https://x.com/akshay_pachaar/status/2005254986339610800?s=12&t=kmKQtU-_oyvUW6FjhHSNTw"
    expected_title = (
        'Akshay 🚀 on X: "This is the DeepSeek moment for Voice AI.\n\n'
        "Chatterbox Turbo is an MIT-licensed voice model that beats ElevenLabs Turbo & Cartesia Sonic 3!\n\n"
        "- <150ms time-to-first-sound\n"
        "- Voice cloning from just 5-second audio\n"
        "- Paralinguistic tags for real human expression\n\n"
        "100% open-source. https://t.co/nu6ZpZDwOt\" / X"
    )
    body = (
        "This is the DeepSeek moment for Voice AI.\n\n"
        "Chatterbox Turbo is an MIT-licensed voice model that beats ElevenLabs Turbo & Cartesia Sonic 3!\n\n"
        "- <150ms time-to-first-sound\n"
        "- Voice cloning from just 5-second audio\n"
        "- Paralinguistic tags for real human expression\n\n"
        "100% open-source."
    )

    from src import preprocess

    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: expected_title)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: body)
    monkeypatch.setattr(preprocess, "detect_content_type_sync", lambda url, timeout=5.0: (ContentType.HTML, "mocked"))
    page = {"id": "8", "title": "", "url": tweet_url, "attachments": [], "raw_content": ""}
    res = preprocess.preprocess_item(page, notion, "cdp")
    assert res["action"] == "backfilled"
    assert notion.titles["8"]["title"] == expected_title

    async def _body(url, cdp_url):
        return body

    monkeypatch.setattr("main.fetch_page_content", _body)
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
    monkeypatch.setattr("main.generate_digest", lambda text: {"tldr": "tldr", "insights": ""})
    result = main.process_item(page, notion, "http://localhost:9222")

    assert result == "success"
    assert notion.classifications["8"]["raw_content"] == body
    assert notion.done["8"]["status"] == notion.status.ready
    assert notion.done["8"]["summary"].startswith("tldr")
