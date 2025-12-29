import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from src.browser import fetch_page_content, fetch_page_title


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


def fetch_title_from_url(url: str, cdp_url: str) -> Optional[str]:
    try:
        return asyncio.run(fetch_page_title(url, cdp_url))
    except Exception as exc:
        logging.warning("Preprocess: fetch_page_title failed for %s: %s", url, exc)
        return None


def _domain_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def _is_meaningful_name(name: str, url: Optional[str]) -> bool:
    """Treat empty/placeholder/domain-like names as missing."""
    cleaned = (name or "").strip()
    if not cleaned:
        return False
    lowered = cleaned.lower()
    if lowered in {"untitled", "new page", "bookmark", "default"}:
        return False
    # names that are just the domain or url are not meaningful
    domain = _domain_from_url(url)
    if domain and (cleaned == domain or cleaned.startswith("http")):
        return False
    return True


def preprocess_item(page: Dict[str, Any], notion: Any, cdp_url: str) -> Dict[str, Any]:
    """Enforce mandatory fields and backfill Name when possible."""
    page_id = page.get("id", "")
    name = (page.get("title") or "").strip()
    url = page.get("url")
    raw_content = (page.get("raw_content") or "").strip()
    attachments: List[str] = page.get("attachments") or []

    has_name = _is_meaningful_name(name, url)
    has_url = bool(url)
    has_content = bool(raw_content or attachments)

    if has_name and not (has_url or has_content):
        notion.mark_as_error(page_id, "missing URL and Content")
        return {"action": "error", "reason": "missing URL/Content"}

    if not has_name and not (has_url or has_content):
        # Fallback for image-only blocks (no URL/content/attachments captured)
        suffix = page_id[-4:] if page_id else "0000"
        title = f"Image-{datetime.now().strftime('%Y%m%d')}-{suffix}"
        notion.set_title(page_id, title, note="Backfilled image placeholder (no URL/Content)")
        return {"action": "backfilled", "title": title}

    if not has_name:
        title = None
        if has_url:
            title = fetch_title_from_url(url, cdp_url)
            if not title:
                text = fetch_text_from_url(url, cdp_url) or ""
                title = derive_title_from_content(text)
        if not title and raw_content:
            title = derive_title_from_content(raw_content)
        if not title and attachments:
            title = attachments[0].split("/")[-1][:140]
        if not title and has_url:
            domain = _domain_from_url(url)
            if domain:
                title = f"Bookmark:{domain}"[:140]
        if not title and not has_url and attachments:
            title = "Image Clip"

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

