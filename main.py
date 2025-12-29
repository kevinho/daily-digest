#!/usr/bin/env python3
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Optional

try:
    from tenacity import RetryError
except Exception:  # pragma: no cover
    RetryError = Exception

from src.browser import fetch_page_content
from src.llm import classify, generate_digest
from src.notion import NotionManager
from src.digest import build_digest
from src.preprocess import preprocess_batch
from src.utils import configure_logging, get_env, get_timezone, normalize_tweet_url
from urllib.parse import urlparse
import os


def is_attachment_unprocessed(url: str) -> bool:
    lowered = url.lower()
    return lowered.endswith((".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"))


def _domain_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return parsed.hostname
    except Exception:
        return None


def _is_meaningful_name(name: str, url: Optional[str]) -> bool:
    cleaned = (name or "").strip()
    if not cleaned:
        return False
    lowered = cleaned.lower()
    if lowered in {"untitled", "new page", "bookmark", "default"}:
        return False
    domain = _domain_from_url(url)
    if domain and (cleaned == domain or cleaned.startswith("http")):
        return False
    return True


def process_item(page: dict, notion: NotionManager, cdp_url: str) -> str:
    page_id = page.get("id", "")
    url = page.get("url")
    source = page.get("source") or "manual"
    attachments = page.get("attachments", [])
    if not url:
        if attachments:
            notion.mark_unprocessed(page_id, "Attachment stored; no URL; OCR out of scope; excluded from digests")
            return "unprocessed"
        else:
            notion.mark_as_error(page_id, "missing url")
            return "error"

    from src.dedupe import canonical_url

    tweet_norm = normalize_tweet_url(url)
    if tweet_norm is None and ("twitter.com" in url.lower() or "x.com" in url.lower()):
        notion.mark_as_error(page_id, "invalid tweet url")
        return "error"
    target_url = tweet_norm or url
    canonical = canonical_url(target_url)
    existing = notion.find_by_canonical(canonical)
    if existing and existing.get("id") != page_id:
        if existing.get("status") in (notion.status.ready, notion.status.pending):
            notion.set_duplicate_of(page_id, existing["id"], f"Duplicate of ready/pending {existing['id']}")
            return "duplicate"
        notion.set_duplicate_of(page_id, existing["id"], f"Duplicate of {existing['id']}")
        return "duplicate"

    # Attachment without OCR support
    if is_attachment_unprocessed(url):
        notion.mark_unprocessed(page_id, "Attachment stored; OCR out of scope; excluded from digests")
        return "unprocessed"

    try:
        text = asyncio.run(fetch_page_content(target_url, cdp_url))
    except RetryError as exc:
        last_exc = getattr(exc, "last_attempt", None)
        if last_exc and last_exc.exception():
            reason = str(last_exc.exception())
        else:
            reason = str(exc)
        notion.mark_as_error(page_id, f"fetch failed: {reason}")
        return "error"
    except Exception as exc:  # catch RuntimeError, etc.
        notion.mark_as_error(page_id, f"fetch failed: {exc}")
        return "error"

    if not text:
        notion.mark_as_error(page_id, "no content")
        return "error"

    # Classification
    classification = classify(text)
    tags = classification.get("tags", [])
    sensitivity = classification.get("sensitivity", "public")
    confidence = float(classification.get("confidence", 0.0))
    rule_version = classification.get("rule_version", "rule-v0")
    prompt_version = classification.get("prompt_version", "prompt-v0")

    notion.set_classification(
        page_id=page_id,
        tags=tags,
        sensitivity=sensitivity,
        confidence=confidence,
        rule_version=rule_version,
        prompt_version=prompt_version,
        raw_content=text,
        canonical_url=canonical,
        source=source,
    )

    summary = generate_digest(text)
    threshold = float(get_env("CONFIDENCE_THRESHOLD", "0.5"))
    summary_text = summary.get("tldr", "")
    insights = summary.get("insights")
    if insights:
        summary_text = (summary_text + "\n" + insights).strip()
    if confidence < threshold:
        notion.mark_as_done(page_id, summary_text, status=notion.status.pending)
        # If title仍不够清晰，用摘要首行回填标题，便于辨识
        title_existing = page.get("title", "")
        if not _is_meaningful_name(title_existing, url):
            fallback_title = summary_text.splitlines()[0][:140] if summary_text else ""
            if fallback_title:
                notion.set_title(page_id, fallback_title, note="Backfilled Name from summary (low confidence)")
        return "success"

    note_status = None
    if source == "plugin":
        note_status = notion.status.ready
    notion.mark_as_done(page_id, summary_text, status=note_status)
    # Ready case也回填标题（若原有标题无意义）
    title_existing = page.get("title", "")
    if not _is_meaningful_name(title_existing, url):
        fallback_title = summary_text.splitlines()[0][:140] if summary_text else ""
        if fallback_title:
            notion.set_title(page_id, fallback_title, note="Backfilled Name from summary")
    return "success"


def run_preprocess(notion: NotionManager, cdp_url: str, scope: str) -> None:
    items = notion.get_pending_tasks()
    stats = preprocess_batch(items, notion, cdp_url)
    logging.info("Preprocess scope=%s results: %s", scope, stats)


def main(digest_window: Optional[str] = None, preprocess_only: bool = False) -> None:
    configure_logging()
    logging.info("Starting orchestrator")
    cdp_url = get_env("CHROME_REMOTE_URL", "http://localhost:9222")
    notion = NotionManager()
    scope = get_env("PREPROCESS_SCOPE", "pending")

    # 预处理必跑：先做字段补齐/校验，再进入抓取与摘要阶段
    run_preprocess(notion, cdp_url, scope)
    if preprocess_only:
        return

    pending = notion.get_pending_tasks()
    counts = {"success": 0, "error": 0, "duplicate": 0, "unprocessed": 0}
    for item in pending:
        result = process_item(item, notion, cdp_url)
        if result in counts:
            counts[result] += 1
    if digest_window:
        logging.info("Manual digest trigger requested for window=%s", digest_window)
        ready = notion.fetch_ready_for_digest(since=None, until=None, include_private=False)
        digest_payload = build_digest(ready)
        num_url = len(digest_payload.get("url_items", []))
        num_note = len(digest_payload.get("note_items", []))
        num_empty = len(digest_payload.get("empty_items", []))
        num_citations = len(digest_payload.get("citations", []))
        logging.info("Digest built: %d url, %d note, %d empty, %d citations", num_url, num_note, num_empty, num_citations)
        now = datetime.now(get_timezone())
        digest_title = f"Digest ({digest_window}) {now.strftime('%Y-%m-%d %H:%M')}"
        metadata = {"window": digest_window, "items": str(len(ready)), "generated_at": now.isoformat()}
        page_id = notion.create_digest_page(digest_title, digest_payload, metadata=metadata)
        if page_id:
            logging.info("Digest page created: %s", page_id)
        else:
            logging.warning("NOTION_DIGEST_PARENT_ID not set; digest page not created")
    logging.info("Ingest results: %s", counts)
    logging.info(
        "METRIC ingest_counts success=%d error=%d duplicate=%d unprocessed=%d",
        counts["success"],
        counts["error"],
        counts["duplicate"],
        counts["unprocessed"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Personal Content Digest orchestrator")
    parser.add_argument("--digest", dest="digest_window", default=None, help="Trigger manual digest window (e.g., daily/weekly/monthly/custom)")
    parser.add_argument(
        "--preprocess",
        dest="preprocess_only",
        action="store_true",
        help="Run fill-missing-fields preprocessing (backfill Name, enforce URL/Content) and exit",
    )
    args = parser.parse_args()
    main(digest_window=args.digest_window, preprocess_only=args.preprocess_only)
