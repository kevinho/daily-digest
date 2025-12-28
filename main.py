#!/usr/bin/env python3
import asyncio
import logging
from typing import Optional

from src.browser import fetch_page_content
from src.llm import generate_digest
from src.notion import NotionManager
from src.utils import configure_logging, get_env


def process_item(page: dict, notion: NotionManager, cdp_url: str) -> None:
    page_id = page.get("id", "")
    url = page.get("url")
    if not url:
        notion.mark_as_error(page_id, "missing url")
        return
    text = asyncio.get_event_loop().run_until_complete(fetch_page_content(url, cdp_url))
    if not text:
        notion.mark_as_error(page_id, "no content")
        return
    summary = generate_digest(text)
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
        # Placeholder: manual digest trigger
        logging.info("Digest trigger requested for window=%s (not implemented)", digest_window)


if __name__ == "__main__":
    main()
