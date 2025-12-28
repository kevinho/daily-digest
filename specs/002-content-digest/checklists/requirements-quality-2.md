# Requirements Quality Checklist v2: Personal Content Digest

**Purpose**: Additional unit tests for requirement clarity/completeness (Notion + Chrome CDP, no OCR phase)
**Created**: 2025-12-28
**Feature**: specs/002-content-digest/spec.md

## Requirement Completeness
- [x] CHK001 Are numeric thresholds defined for low confidence (e.g., <0.5) and mapped to status=pending/excluded rules? [Completeness, Spec §FR-004]
- [x] CHK002 Are sensitivity level rules (public/internal/private) fully specified for digest inclusion/redaction and storage? [Completeness, Spec §FR-013]
- [x] CHK003 Are unprocessed attachment rules documented (PDF/image stored, marked unprocessed, excluded from digests) with required properties? [Completeness, Spec §FR-002, Edge Cases]
- [x] CHK004 Is the backlog visibility requirement (pending/queue surfacing) defined for rate limits/offline cases? [Completeness, Edge Cases]
- [x] CHK005 Is delete/mark-sensitive propagation behavior specified (timing ≤24h, where confirmed)? [Completeness, Spec §FR-013, SC-005]

## Requirement Clarity
- [x] CHK006 Is “canonical URL” normalization defined (scheme/params, trailing slash, tracking params) and hash algorithm named? [Clarity, Spec §FR-005]
- [x] CHK007 Are notification channels/timing/quiet hours spelled out (Notion mentions/email; when triggered)? [Clarity, Spec §FR-012]
- [x] CHK008 Are redaction rules for sensitive content stated (what fields/sections are removed, how citations are handled)? [Clarity, Spec §FR-013]

## Requirement Consistency
- [x] CHK009 Do status transitions (pending/ready/excluded/unprocessed) align across intake, dedupe, digest inclusion, and corrections? [Consistency, Spec §FR-002, §FR-004, §FR-010, §FR-013]
- [x] CHK010 Are p95 performance targets consistent with measurement points (capture path via Chrome CDP vs Notion write) and success criteria SC-001..SC-003? [Consistency, Spec §SC-001..SC-003]

## Measurability & Traceability
- [x] CHK011 Are methods to measure p95 (timestamps collected where?) and low-confidence queue size documented? [Measurability, Spec §SC-001..SC-003]
- [x] CHK012 Are correction triggers traceable (which Notion fields/comments cause re-run) and logged? [Traceability, Spec §FR-011]

## Scenario & Edge Coverage
- [x] CHK013 Are authenticated-page capture requirements via Chrome CDP explicit (what happens on auth failure/captcha)? [Coverage, Architecture Constraint]
- [x] CHK014 Are duplicate bursts across devices covered with conflict resolution order and user-facing indication? [Edge Case, Spec §FR-005]

## Dependencies & Assumptions
- [x] CHK015 Are external dependency failures (Notion, OpenAI, Chrome CDP) given fallback/retry limits and user notification requirements? [Dependency, Spec §Assumptions]
