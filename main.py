#!/usr/bin/env python3
import argparse
import asyncio
import logging
from typing import Optional

from src.browser import fetch_page_content
from src.llm import classify, generate_digest
from src.notion import NotionManager
from src.utils import configure_logging, get_env


def is_attachment_unprocessed(url: str) -> bool:
    lowered = url.lower()
    return lowered.endswith((".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp"))


def process_item(page: dict, notion: NotionManager, cdp_url: str) -> None:
    page_id = page.get("id", "")
    url = page.get("url")
    if not url:
        notion.mark_as_error(page_id, "missing url")
        return

    # Dedupe by canonical URL
    from src.dedupe import canonical_url

    canonical = canonical_url(url)
    existing = notion.find_by_canonical(canonical)
    if existing and existing.get("id") != page_id:
        notion.set_duplicate_of(page_id, existing["id"], f"Duplicate of {existing['id']}")
        return

    # Attachment without OCR support
    if is_attachment_unprocessed(url):
        notion.mark_unprocessed(page_id, "Attachment stored; OCR out of scope; excluded from digests")
        return

    text = asyncio.get_event_loop().run_until_complete(fetch_page_content(url, cdp_url))
    if not text:
        notion.mark_as_error(page_id, "no content")
        return

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
    )

    summary = generate_digest(text)
    threshold = float(get_env("CONFIDENCE_THRESHOLD", "0.5"))
    if confidence < threshold:
        notion.mark_as_done(page_id, summary.get("tldr", ""), status=notion.status.pending)
        return

    notion.mark_as_done(page_id, summary.get("tldr", ""))


def main(digest_window: Optional[str] = None) -> None:
    configure_logging()
    logging.info("Starting orchestrator")
    cdp_url = get_env("CHROME_REMOTE_URL", "http://localhost:9222")
    notion = NotionManager()
    pending = notion.get_pending_tasks()
    for item in pending:
        process_item(item, notion, cdp_url)
    if digest_window:
        logging.info("Manual digest trigger requested for window=%s (not implemented)", digest_window)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Personal Content Digest orchestrator")
    parser.add_argument("--digest", dest="digest_window", default=None, help="Trigger manual digest window (e.g., daily/weekly/monthly/custom)")
    args = parser.parse_args()
    main(digest_window=args.digest_window)
