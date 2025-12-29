import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.browser import fetch_page_content


def _first_non_empty_line(text: str) -> Optional[str]:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:140]
    return None


def derive_title_from_content(content: Optional[str]) -> Optional[str]:
    if not content:
        return None
    return _first_non_empty_line(content)


def fetch_text_from_url(url: str, cdp_url: str) -> Optional[str]:
    try:
        return asyncio.run(fetch_page_content(url, cdp_url))
    except Exception as exc:
        logging.warning("Preprocess: fetch_page_content failed for %s: %s", url, exc)
        return None


def preprocess_item(page: Dict[str, Any], notion: Any, cdp_url: str) -> Dict[str, Any]:
    """Enforce mandatory fields and backfill Name when possible."""
    page_id = page.get("id", "")
    name = (page.get("title") or "").strip()
    url = page.get("url")
    raw_content = (page.get("raw_content") or "").strip()
    attachments: List[str] = page.get("attachments") or []

    has_name = bool(name)
    has_url = bool(url)
    has_content = bool(raw_content or attachments)

    if has_name and not (has_url or has_content):
        notion.mark_as_error(page_id, "missing URL and Content")
        return {"action": "error", "reason": "missing URL/Content"}

    if not has_name and not (has_url or has_content):
        notion.mark_as_error(page_id, "missing Name and URL/Content")
        return {"action": "error", "reason": "missing all required fields"}

    if not has_name:
        title = None
        if has_url:
            text = fetch_text_from_url(url, cdp_url) or ""
            title = derive_title_from_content(text)
        if not title and raw_content:
            title = derive_title_from_content(raw_content)
        if not title and attachments:
            title = attachments[0].split("/")[-1][:140]

        if title:
            notion.set_title(page_id, title, note="Backfilled Name during preprocessing")
            return {"action": "backfilled", "title": title}

        notion.mark_as_error(page_id, "unable to backfill Name from URL/Content")
        return {"action": "error", "reason": "backfill failed"}

    return {"action": "skip"}


def preprocess_batch(pages: List[Dict[str, Any]], notion: Any, cdp_url: str) -> Dict[str, int]:
    counters = {"backfilled": 0, "error": 0, "skip": 0}
    for page in pages:
        result = preprocess_item(page, notion, cdp_url)
        action = result.get("action", "skip")
        if action in counters:
            counters[action] += 1
        else:
            counters["skip"] += 1
    return counters

