# Quickstart: Personal Content Digest (Notion + Chrome)

## Prerequisites
- Python 3.11 + venv
- Notion integration token with access to the target database
- Notion Database ID prepared with schema from data-model.md
- OpenAI API key (for summarization)
- Chrome installed and logged in (for CDP); Notion Web Clipper/share for manual capture

## Setup
1) Copy `.env.example` → `.env` (create if absent) and set:
   - `NOTION_TOKEN=<secret>`
   - `NOTION_ITEM_DB_ID=<db_id>`
   - `OPENAI_API_KEY=<key>`
   - `TIMEZONE=<e.g., Asia/Shanghai>`
2) Create venv: `python3 -m venv .venv && source .venv/bin/activate`.
3) Install deps: `pip install -r requirements.txt`.
4) Install Playwright browsers (once): `python -m playwright install chromium`.
5) Start Chrome for CDP: `./start_chrome.sh` (opens with `--remote-debugging-port=9222` and user-data-dir).
6) Run tests: `pytest`.

## Capture Flow (Chrome/mobile)
- Primary: Notion clipper/share → items land in Notion (source of truth).
- For gated pages, open in logged-in Chrome, then the orchestrator fetches via CDP to extract HTML/text.

## CLI / Scripts (planned)
- Orchestrator loop: `python main.py --once` (or cron/invoke for schedule).
- Fetch single URL dry-run: `python -m src.browser --url "https://..."`.
- Generate digest for range: `python main.py --digest --since "2025-12-01" --until "2025-12-02"`.

## Notes
- Respect Notion rate limit (~3 rps); backoff with jitter; surface pending ops.
- Low-confidence items remain pending and are excluded from digests until reviewed in Notion.
- Digests are written as Notion pages with citations back to entries.
