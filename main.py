#!/usr/bin/env python3
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Optional

from src.browser import fetch_page_content
from src.llm import classify, generate_digest
from src.notion import NotionManager
from src.digest import build_digest
from src.utils import configure_logging, get_env, get_timezone, normalize_tweet_url


def is_attachment_unprocessed(url: str) -> bool:
    lowered = url.lower()
    return lowered.endswith((".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"))


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
    except Exception as exc:  # catch RetryError/RuntimeError
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
        return

    note_status = None
    if source == "plugin":
        note_status = notion.status.ready
    notion.mark_as_done(page_id, summary_text, status=note_status)
    return "success"


def main(digest_window: Optional[str] = None) -> None:
    configure_logging()
    logging.info("Starting orchestrator")
    cdp_url = get_env("CHROME_REMOTE_URL", "http://localhost:9222")
    notion = NotionManager()
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
        logging.info("Digest built with %d sections, %d citations", len(digest_payload["sections"]), len(digest_payload["citations"]))
        now = datetime.now(get_timezone())
        digest_title = f"Digest ({digest_window}) {now.strftime('%Y-%m-%d %H:%M')}"
        metadata = {"window": digest_window, "generated_at": now.isoformat()}
        page_id = notion.create_digest_page(digest_title, digest_payload["sections"], digest_payload["citations"], metadata=metadata)
        if page_id:
            logging.info("Digest page created: %s", page_id)
        else:
            logging.warning("NOTION_DIGEST_PARENT_ID not set; digest page not created")
    logging.info("Ingest results: %s", counts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Personal Content Digest orchestrator")
    parser.add_argument("--digest", dest="digest_window", default=None, help="Trigger manual digest window (e.g., daily/weekly/monthly/custom)")
    args = parser.parse_args()
    main(digest_window=args.digest_window)
