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
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: "Title from page title")
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Title from page\nBody")

    page = {"id": "1", "title": "", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "http://localhost:9222")
    assert result["action"] == "backfilled"
    assert notion.titles["1"]["title"].startswith("Title from page")


def test_backfill_from_content_when_url_empty(monkeypatch):
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
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
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
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


def test_domain_placeholder_backfills_with_bookmark(monkeypatch):
    notion = StubNotion()
    # Simulate fetch failure to force domain fallback
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "")
    page = {"id": "d", "title": "https://example.com", "url": "https://example.com/post", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["d"]["title"].startswith("Bookmark:example.com")


def test_image_clip_name_when_only_attachment():
    notion = StubNotion()
    page = {"id": "e", "title": "", "url": None, "attachments": ["https://files/notion/image.png"], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["e"]["title"] in ["image.png", "Image Clip"]


def test_title_prefers_page_title_over_text(monkeypatch):
    notion = StubNotion()
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: "Preferred Title")
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: "Fallback text title")
    page = {"id": "f", "title": "", "url": "http://example.com", "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["f"]["title"] == "Preferred Title"


def test_wechat_url_backfills_from_content(monkeypatch):
    """
    For weixin articles where page title may be blocked/empty,
    we should still backfill from content first line.
    """
    notion = StubNotion()
    wechat_url = "https://mp.weixin.qq.com/s/xNs46pBq8pWhMGRWpFieyQ"
    expected_title = "对话尤瓦尔·赫拉利：人类对秩序的渴求先于真相，是互联网和AI控制个人的首要原因"
    # Prefer page/og:title when available; fall back to content otherwise.
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: expected_title)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: None)
    raw = "腾讯科技：您在书中提到处理这类问题的方法是对齐。\n后续内容……"
    page = {"id": "g", "title": "", "url": wechat_url, "attachments": [], "raw_content": raw}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["g"]["title"] == expected_title


def test_tweet_blocked_uses_content_summary(monkeypatch):
    """
    For a blocked tweet page, if we can't fetch title but have content,
    we should backfill from the content summary/first line.
    """
    notion = StubNotion()
    tweet_url = "https://x.com/demishassabis/status/2005358760047562802?s=12&t=kmKQtU-_oyvUW6FjhHSNTw"
    tweet_text = "Demis Hassabis on X: \"Amazing work from the incredibly talented Director Greg Kohs, Producers Gary Kreig &amp; Jonathan Fildes, and a wonderful score from the maestro Dan Deacon - enjoy! https://t.co/fagdivZ9qN\" / X"
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: None)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: tweet_text)
    page = {"id": "h", "title": "", "url": tweet_url, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert tweet_text[:120] in notion.titles["h"]["title"]


def test_tweet_title_prefers_page_title(monkeypatch):
    """
    When tweet page title is available, prefer it over content snippet.
    """
    notion = StubNotion()
    tweet_url = "https://x.com/demishassabis/status/2005358760047562802?s=12&t=kmKQtU-_oyvUW6FjhHSNTw"
    title = 'Demis Hassabis on X: "Amazing work from the incredibly talented Director Greg Kohs, Producers Gary Kreig & Jonathan Fildes, and a wonderful score from the maestro Dan Deacon - enjoy! https://t.co/fagdivZ9qN" / X'
    body = "Amazing work from the incredibly talented Director Greg Kohs, Producers Gary Kreig & Jonathan Fildes, and a wonderful score from the maestro Dan Deacon - enjoy!"
    monkeypatch.setattr(preprocess, "fetch_title_from_url", lambda url, cdp: title)
    monkeypatch.setattr(preprocess, "fetch_text_from_url", lambda url, cdp: body)
    page = {"id": "i", "title": "", "url": tweet_url, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["i"]["title"] == title


def test_image_block_placeholder_when_no_url_content(monkeypatch):
    notion = StubNotion()

    class FakeDt:
        @staticmethod
        def now():
            class D:
                def strftime(self, fmt):
                    return "20250101"
            return D()

    monkeypatch.setattr(preprocess, "datetime", FakeDt)
    page = {"id": "img1234", "title": "", "url": None, "attachments": [], "raw_content": ""}
    result = preprocess.preprocess_item(page, notion, "cdp")
    assert result["action"] == "backfilled"
    assert notion.titles["img1234"]["title"].startswith("Image-20250101-1234")

