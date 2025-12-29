# Tasks: Item Preprocessing (Name + URL/Content completeness)

**Input**: Design docs at `specs/001-item-preprocess/`  
**Prerequisites**: `plan.md`, `spec.md` (user stories), constitution constraints (no OCR), Notion data source schema in place.

Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 [P] Confirm Notion schema fields exist (`Name`/title, `URL`, `Raw Content`/files, `Status`, `Reason`/Notes); update scripts if needed (`scripts/notion_align_schema.py`, `scripts/fix_schema_direct.py`).
- [x] T002 [P] Add env/config defaults for preprocessing trigger (e.g., `PREPROCESS_SCOPE`, log level) in `.env.example` and `src/utils.py` if needed.

---

## Phase 2: Foundational (Blocking)

- [x] T010 [P] Create `src/preprocess.py` with helpers: detect missing mandatory fields, derive title from URL/content, annotate actions (backfilled/error/skip), idempotent behavior.
- [x] T011 [P] Add unit test scaffolding in `tests/` (e.g., `tests/test_preprocess.py`) covering: missing Name + URL title; missing Name + Content-derived title; Name present but no URL/Content → Error; already valid item → no-op.

**Checkpoint**: Preprocessing core logic is independently testable.

---

## Phase 3: User Story 1 - Backfill missing Name (Priority: P1) 🎯

- [x] T020 [US1] Implement URL title extraction (reuse `src/browser.fetch_page_content` or lightweight fetch) and content-derived title heuristic (first heading/first line) in `src/preprocess.py`.
- [x] T021 [US1] Integrate backfill path into routine: when Name empty and URL or Content present, set Name from title; record action/reason.
- [x] T022 [P][US1] Tests: URL path succeeds; unreachable URL falls back to Content; Content-only item derives sensible Name; nonsense/empty content → Error.

---

## Phase 4: User Story 2 - Enforce mandatory fields (Priority: P1)

- [x] T030 [US2] Implement validation: require Name and at least one of URL or Content/Files; if Name present but URL+Content absent, mark Error with reason; idempotent on rerun.
- [x] T031 [P][US2] Tests: Name+URL ok; Name+Content ok; Name only → Error; empty Name + URL/Content handled by US1 before this step.

---

## Phase 5: User Story 3 - Manual/automatic trigger (Priority: P2)

- [x] T040 [US3] Add manual CLI entry (e.g., `python main.py --preprocess`) to run fill-missing-fields over pending scope; log actions summary.
- [x] T041 [US3] Add optional auto trigger hook (document cron/apscheduler stub or flag) reusing the same routine; ensure idempotent across runs.
- [x] T042 [P][US3] Tests/integration: invoke trigger on a mixed batch; verify backfilled names, errors set, valid items unchanged.

---

## Phase 6: Polish & Cross-Cutting

- [x] T050 [P] Annotate audit notes/reasons in Notion updates (e.g., `Reason`/`Notes` property) for backfilled/error/skip outcomes.
- [x] T051 [P] Update `specs/001-item-preprocess/quickstart.md` with run commands and expected outcomes; add troubleshooting for missing schema/permissions.
- [x] T052 [P] Add logging/metrics hooks (per-item counts for backfilled/error/skip) and ensure rerun idempotency is documented.

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → User stories (Phases 3–5) → Polish.  
- User stories are independent after foundational tasks; tests marked [P] can run in parallel.  
- Avoid changing valid items; reruns must be safe (idempotent).

