#!/usr/bin/env python3
"""
Debug helper for Twitter/X content capture.

Usage:
    python scripts/debug_twitter_content.py --url https://x.com/... --cdp http://localhost:9222

What it does:
1) Connects to an existing Chrome (CDP) to reuse your logged-in session.
2) Opens the tweet URL, waits 10 seconds.
3) Saves:
   - Full-page screenshot -> debug_content_screenshot.png
   - Full HTML dump       -> debug_content_dump.html
4) Prints locator count for div[data-testid="tweetText"] so we can see if Playwright finds the tweet body.
"""

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def main(url: str, cdp_url: str, screenshot: str, html_dump: str) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)

        # Reuse first context if exists, otherwise create one with a sensible UA/viewport
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
        else:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                device_scale_factor=2,
                is_mobile=False,
                has_touch=False,
                locale="en-US",
                timezone_id="America/Los_Angeles",
            )

        page = await context.new_page()

        print(f"[debug] Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        # Give time for dynamic content / JS walls to settle
        await page.wait_for_timeout(10000)

        # Capture locator count for tweet text
        tweet_locator = page.locator('div[data-testid="tweetText"]')
        count = await tweet_locator.count()
        print(f"[debug] tweetText locator count: {count}")

        # Save screenshot and HTML
        await page.screenshot(path=screenshot, full_page=True)
        html = await page.content()
        Path(html_dump).write_text(html, encoding="utf-8")
        print(f"[debug] Saved screenshot -> {screenshot}")
        print(f"[debug] Saved HTML dump -> {html_dump}")

        await page.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug Twitter/X content capture")
    parser.add_argument("--url", required=True, help="Tweet URL to debug")
    parser.add_argument("--cdp", default="http://localhost:9222", help="CDP endpoint for existing Chrome")
    parser.add_argument("--screenshot", default="debug_content_screenshot.png", help="Output screenshot path")
    parser.add_argument("--html", default="debug_content_dump.html", help="Output HTML dump path")
    args = parser.parse_args()

    asyncio.run(main(args.url, args.cdp, args.screenshot, args.html))

