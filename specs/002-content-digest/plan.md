# Implementation Plan: Personal Content Digest

**Branch**: `002-content-digest` | **Date**: 2025-12-28 | **Spec**: specs/002-content-digest/spec.md  
**Input**: Feature specification from `/specs/002-content-digest/spec.md`  
**User Input**: "使用 notion+chrome 浏览器debug 的方案进行实现。"

## Summary

- Notion Database is the single source of truth; capture occurs via Chrome share/clipper and a CDP-connected Chrome session to pull authenticated page content, then create/update Notion entries with source/device/timestamp.
- Python orchestrator: `start_chrome.sh` launches Chrome with remote debugging; `main.py` loops pending Notion rows, fetches page HTML via `src/browser.py`, summarizes via `src/llm.py`, writes back via `src/notion.py`.
- Auto-tag, sensitivity, and dedupe (canonical URL/hash) live in Notion; low-confidence items are held from digests; digests render as Notion pages with citations back to entries. Attachments (PDF/images) are stored and marked unprocessed (no OCR in this phase). Performance targets remain capture p95 ≤ 5s, digest batch p95 ≤ 60s.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: playwright (CDP connect to Chrome), trafilatura (HTML → text), notion-client (Python SDK), openai (gpt-4o), tenacity/backoff, cron/apscheduler, dotenv  
**Storage**: Notion Database (single DB + derived views); attachments stored in Notion files/links  
**Testing**: pytest + responses/vcr for Notion/LLM mocks; playwright in headful CDP for smoke; fixture-based tests for dedupe/classification  
**Target Platform**: macOS desktop (personal) runner with manual CLI triggers for digest; Chrome with `--remote-debugging-port=9222` for capture/debug  
**Project Type**: single project (scripts/CLI + worker loop)  
**Performance Goals**: capture+classify p95 ≤ 5s per item; digest generation p95 ≤ 60s per schedule; backlog visibility if exceeded  
**Constraints**: Notion API rate limit (~3 rps sustained); avoid storing browser cookies (use user profile via Chrome debug instance); sensitive content redaction before sharing; offline capture queued and backfilled; handle Chrome CDP reconnect  
**Scale/Scope**: Single user; ~100 items/day; digests daily/weekly/monthly

## Constitution Check

- Trustworthy Intake & Consent: user-initiated share from logged-in browser/mobile; store source/device/timestamp; reject disallowed sources. **Status: PASS**
- Structured Capture: Notion schema enforces raw content/URL, normalized text, tags, sensitivity, confidence, canonical URL, status. **Status: PASS**
- Privacy/Security/Least Access: no stored credentials; Notion token scoped to DB; sensitive flag controls digest inclusion; redaction before sharing; deletions honored. **Status: PASS**
- Summarization Quality & Traceability: digests cite Notion entry links; include scope, assumptions, confidence; block low-citation outputs. **Status: PASS**
- Feedback & Safe Automation: Notion edits/comments captured as corrections; low-confidence queue requires review before digests. **Status: PASS**
- Operational Constraints: capture p95 ≤ 5s; digest p95 ≤ 60s; lineage preserved across stages; evaluation assets versioned. **Status: PASS (monitor in quickstart/runbook)**

## Project Structure

### Documentation (this feature)

```text
specs/002-content-digest/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── http.md
└── tasks.md             # via /speckit.tasks
```

### Source Code (repository root)

```text
start_chrome.sh      # launch Chrome with remote debugging and user-data-dir
main.py              # orchestrator loop
requirements.txt
src/
├── browser.py       # CDP connect, page fetch, trafilatura extract
├── notion.py        # Notion read/write, dedupe, status updates
├── llm.py           # prompt + OpenAI summarize/classify
├── dedupe.py        # canonical URL/hash helpers
└── utils.py         # logging, timezones, backoff

tests/
├── test_browser.py
├── test_notion.py
├── test_llm.py
└── fixtures/
```

**Structure Decision**: Single Python project with Chrome CDP for capture and Notion as storage; no additional DB/services.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _None_ |  |  |
