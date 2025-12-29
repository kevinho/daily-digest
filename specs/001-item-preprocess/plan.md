# Implementation Plan: Item Preprocessing (Name + URL/Content completeness)

**Branch**: `001-item-preprocess` | **Date**: 2025-12-29 | **Spec**: specs/001-item-preprocess/spec.md  
**Input**: Feature specification from `/specs/001-item-preprocess/spec.md`

## Summary

Implement a preprocessing routine that enforces mandatory fields per item: Name is required, and at least one of URL or Content (raw text/files) must exist. Missing Name is backfilled from URL title or Content-derived title; if Name exists but both URL and Content are absent, mark Error with a reason. Provide manual and optional automatic triggers to run the fill-missing-fields logic; actions are idempotent and annotated (backfilled, errored, skipped).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: notion-client (Data Source DB), Playwright (CDP fetch already in repo), trafilatura (text extraction), openai (LLM summaries), tenacity/backoff (retry), python-dotenv (env), httpx/requests (HTTP).  
**Storage**: Notion database (data source) as single source of truth.  
**Testing**: pytest (unit/integration already present).  
**Target Platform**: macOS CLI runner with Chrome remote debugging (personal machine).  
**Project Type**: Single CLI/batch pipeline (Python modules under `src/`, scripts under `scripts/`).  
**Performance Goals**: Preprocessing up to ~200 items in ≤1 minute (aligns with SC-003); individual item field check/backfill ≤5s p95.  
**Constraints**: No OCR/PDF processing (attachments stored, marked unprocessed); respect Notion API limits and status/select schema; maintain lineage and audit annotations; avoid altering items already valid; idempotent reruns.  
**Scale/Scope**: Personal backlog scale (hundreds to low thousands of items); manual + optional scheduled trigger.

## Constitution Check

- Trustworthy Intake & Consent: Use existing provenance in Notion; do not fabricate sources; errors flagged, not silently ingested.  
- Structured Capture Before Processing: Ensure Name + URL/Content present; when backfilled, record rule/marker; low-confidence/failed backfill marked Error for manual triage.  
- Privacy/Security: No new data sharing; stay within Notion; attachments unchanged; no OCR of PDFs/images.  
- Summarization Quality & Traceability: This module only prepares items; must annotate actions/reasons for traceability.  
- Operational Constraints: PDFs/images remain unprocessed; lineage from raw→normalized maintained; performance targets observed.  
**Gate Result**: Pass (no constitution violations identified for planned scope).

## Project Structure

### Documentation (this feature)

```text
specs/001-item-preprocess/
├── plan.md          # This file (/speckit.plan output)
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── quickstart.md    # Phase 1 output
├── contracts/       # Phase 1 output (if APIs/forms needed)
└── tasks.md         # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── browser.py       # CDP fetch/text extraction (existing)
├── notion.py        # Notion manager, status/property helpers
├── llm.py           # LLM calls (existing)
├── dedupe.py        # Canonical URL/content hash (existing)
├── digest.py        # Digest builder (existing)
├── utils.py         # Env/timezone/logging
└── __init__.py

main.py              # Orchestrator/CLI entry
scripts/
├── notion_align_schema.py
├── fix_schema_direct.py
├── db_crud_demo.py
└── printenv.py

tests/
├── test_ingest_integration.py
├── test_dedupe_confidence.py
├── test_digest.py
├── test_llm.py
└── conftest.py
```

**Structure Decision**: Reuse existing single-project Python layout; add preprocessing routines/trigger inside `main.py` and helper modules under `src/` as needed; no new packages/repos.

## Complexity Tracking

No constitution violations; complexity table not required.
