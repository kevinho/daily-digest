import asyncio
from typing import Optional

from playwright.async_api import async_playwright
import trafilatura


async def fetch_page_content(url: str, cdp_url: str = "http://localhost:9222") -> Optional[str]:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="load")
            html = await page.content()
            text = trafilatura.extract(html)
            return text
        finally:
            await page.close()
            await browser.close()


def fetch_page_content_sync(url: str, cdp_url: str = "http://localhost:9222") -> Optional[str]:
    return asyncio.get_event_loop().run_until_complete(fetch_page_content(url, cdp_url))
