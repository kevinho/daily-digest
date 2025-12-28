# Tasks: Personal Content Digest

**Input**: Design documents from `/specs/002-content-digest/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Tests**: Not explicitly requested; add tests where risk is higher (browser fetch, summarization correctness, Notion I/O).

## Phase 1: Setup (Shared Infrastructure)
- [X] T001 Create project structure and files per plan: start_chrome.sh, main.py, requirements.txt, src/browser.py, src/notion.py, src/llm.py, src/dedupe.py, src/utils.py, tests/fixtures/. 
- [X] T002 Add Python toolchain: .python-version/.tool-versions (3.11), venv instructions, pip config if needed.
- [X] T003 Populate requirements.txt with playwright, trafilatura, notion-client, openai, tenacity, python-dotenv, apscheduler/cron, logging deps.
- [X] T004 Add .env.example with NOTION_TOKEN, NOTION_DATABASE_ID, OPENAI_API_KEY, TIMEZONE, CHROME_REMOTE_URL, USER_DATA_DIR.
- [X] T005 Initialize basic logging/config loader in src/utils.py (env parsing, timezone handling).

## Phase 2: Foundational (Blocking Prerequisites)
- [X] T006 Implement start_chrome.sh to launch Chrome with --remote-debugging-port=9222 and user-data-dir, fail clearly if Chrome missing.
- [X] T007 Implement src/notion.py NotionManager skeleton: init client, read pending items (Status="To Read"/pending), update status/summary, mark error.
- [X] T008 Implement src/dedupe.py helpers: canonical_url normalize, content hash, duplicate_of resolution rules.
- [X] T009 Implement src/browser.py CDP connector using playwright.connect_over_cdp, page fetch, HTML extraction, trafilatura.extract to text; include timeout/retry/backoff hooks.
- [X] T010 Wire main.py orchestrator skeleton: loop pending items → fetch → summarize placeholder → write back; include graceful shutdown and backoff on rate limits.
- [X] T011 Add pytest scaffolding and fixtures directory; smoke test placeholders for notion/browser modules.

## Phase 3: User Story 1 - Capture & Classify via Notion Inbox (Priority: P1)
**Goal**: Items from share/clipper/URL land in Notion with metadata, normalized text (when available), tags/sensitivity, dedupe, confidence; attachments without text are marked unprocessed and excluded from digests; low-confidence held from digests.
**Independent Test**: Submit URL/text/file/image; verify Notion row has source/device/timestamp/type, normalized text when available, tags/sensitivity/confidence, dedupe linking, unprocessed marker for non-text attachments; low-confidence marked pending/excluded from digests.

- [ ] T012 [US1] Finalize Notion schema mapping in src/notion.py (properties for source, device, timestamp, type, tags, sensitivity, confidence, status, canonical_url, duplicate_of, rule_version, prompt_version). [Gap]
- [ ] T013 [US1] Implement classification hook in src/llm.py (or rule+LLM hybrid placeholder) returning tags, sensitivity, confidence, prompt_version; integrate rule_version placeholders. [Gap]
- [ ] T014 [US1] Integrate dedupe logic in main.py: canonical URL/hash check via NotionManager before processing; link duplicates. [Gap]
- [ ] T015 [US1] Implement text normalization in src/browser.py for HTML/text; detect PDF/image and mark as unprocessed (no OCR), persisting attachment link. [Gap]
- [ ] T016 [US1] Update main.py to set status pending/ready/excluded based on confidence/sensitivity rules. [Gap]
- [ ] T017 [US1] Add pytest cases for dedupe rules and confidence gating (unit, no external calls). [P] [US1] tests/test_dedupe.py, tests/test_confidence.py. [Gap]
- [ ] T018 [US1] Add integration test with mocked Notion and browser to ensure a URL becomes a normalized Notion entry with tags/sensitivity/confidence. [US1] tests/integration/test_ingest.py. [Gap]

## Phase 4: User Story 2 - Scheduled Personal Digests in Notion (Priority: P2)
**Goal**: Generate digests (daily/weekly/monthly/ad-hoc) with topic grouping, citations to Notion entries, redaction for sensitive items; manual trigger on personal macOS (CLI) before any automation.
**Independent Test**: With ready items in Notion, run manual CLI digest; verify Notion digest page created with sections, citations to entries, excludes low-confidence/sensitive items per rules.

- [ ] T019 [US2] Implement digest query/filter in src/notion.py for time window, status=ready, sensitivity rules. [Gap]
- [ ] T020 [US2] Implement summarization prompt in src/llm.py: TL;DR + key insights with citations placeholders. [Gap]
- [ ] T021 [US2] Implement digest builder in src/digest.py (create new file) to assemble sections, apply redaction, and write Notion page with backlinks. [Gap]
- [ ] T022 [US2] Implement manual CLI trigger in main.py for daily/weekly/monthly/ad-hoc digests on macOS host (no scheduler yet). [Gap]
- [ ] T023 [US2] Add unit test for digest grouping/redaction logic with fixtures. [P] [US2] tests/test_digest.py. [Gap]

## Phase 5: User Story 3 - Search, Review & Corrections in Notion (Priority: P3)
**Goal**: Search/filter in Notion views; corrections to tags/summaries affect future outputs and exclusions.
**Independent Test**: Edit tags/sensitivity/summary in Notion; ensure future digests use corrected data; low-confidence queue can be cleared.

- [ ] T024 [US3] Document Notion views/filters setup in quickstart.md (tag/sensitivity/source/time range) and ensure schema supports needed filters. [Gap]
- [ ] T025 [US3] Implement corrections handling in main.py/notion.py: detect changed tags/sensitivity/notes and re-run classification/digest inclusion. [Gap]
- [ ] T026 [US3] Add test to verify corrections propagate to digest inclusion/exclusion. [US3] tests/integration/test_corrections.py. [Gap]

## Phase 6: Polish & Cross-Cutting Concerns
- [ ] T027 Harden backoff/retry and error surfacing for Notion rate limits and Chrome CDP disconnects. [Gap]
- [ ] T028 Add logging/metrics hooks (timings for SC-001..003, queue sizes, failures). [Gap]
- [ ] T029 Add docs: expand quickstart.md with CDP troubleshooting, rate-limit/backlog visibility, and testing commands. [Gap]
- [ ] T030 Add safety checks: redact sensitive content before external LLM calls; ensure deletions/mark-sensitive propagate within 24h (SC-005). [Gap]

## Dependencies & Execution Order
- Setup (Phase 1) → Foundational (Phase 2) → US1 (P1) → US2 (P2) → US3 (P3) → Polish.
- US2 depends on US1 data readiness; US3 depends on US1 schema and status handling.

## Parallel Opportunities
- Phase 1: T003 requirements.txt, T004 .env.example, T005 utils can run in parallel after T001/T002 skeleton.
- Phase 2: T007, T008, T009 can proceed in parallel after T006; T010 depends on them.
- US1: T017 (tests) parallel with T015; T018 after T014–T016.
- US2: T023 parallel with T020/T021 once digest builder drafted.
- US3: T024 docs can start after US1 schema; T026 after T025.

## Implementation Strategy
- MVP: Complete Phases 1–2 and US1 to enable reliable intake/classify/dedupe in Notion. Run on personal macOS host.
- Incremental: Add US2 digests next as manual triggers (daily/weekly/monthly runs invoked by CLI), then US3 corrections/search. Polish last.
