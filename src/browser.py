import asyncio
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=1, max=4))
async def fetch_page_content(url: str, cdp_url: str = "http://localhost:9222", timeout_ms: int = 15000) -> Optional[str]:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="load", timeout=timeout_ms)
            html = await page.content()
            text = trafilatura.extract(html)
            return text
        except PlaywrightTimeoutError:
            return None
        finally:
            await page.close()
            await browser.close()


def fetch_page_content_sync(url: str, cdp_url: str = "http://localhost:9222", timeout_ms: int = 15000) -> Optional[str]:
    return asyncio.get_event_loop().run_until_complete(fetch_page_content(url, cdp_url, timeout_ms))
