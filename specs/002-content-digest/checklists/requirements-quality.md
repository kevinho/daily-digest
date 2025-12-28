# Requirements Quality Checklist: Personal Content Digest

**Purpose**: Unit tests for requirements wording and completeness (Notion + Chrome CDP flow)
**Created**: 2025-12-28
**Feature**: specs/002-content-digest/spec.md

## Requirement Completeness
- [x] CHK001 Are intake requirements explicit for all capture channels (browser share/clipper, mobile share) including required properties (source, device, timestamp, type)? [Completeness, Spec §FR-001]
- [x] CHK002 Are classification requirements explicit for every captured type (url/text/file/image/pdf) including OCR/normalization expectations? [Completeness, Spec §FR-002]
- [x] CHK003 Are deduplication rules fully specified (canonical URL vs hash priority, tie-break, how duplicates are recorded)? [Completeness, Spec §FR-005]
- [x] CHK004 Are digest generation inputs and outputs defined for each schedule (daily/weekly/monthly) and ad-hoc ranges, including required citations? [Completeness, Spec §FR-008, §FR-009]
- [x] CHK005 Are feedback/correction flows documented for both tags and summaries, including how updates propagate to future digests? [Completeness, Spec §FR-011]

## Requirement Clarity
- [x] CHK006 Is "low confidence" threshold defined quantitatively and does the spec state what properties mark such items in Notion? [Clarity, Spec §FR-004]
- [x] CHK007 Are sensitivity levels (public/internal/private) defined with explicit rules for digest inclusion/redaction? [Clarity, Spec §FR-013]
- [x] CHK008 Are notification quiet hours and delivery channels (Notion mentions/email) specified with conditions and timing? [Clarity, Spec §FR-012]
- [x] CHK009 Is "canonical URL" definition precise (normalized scheme/params) and is hash function specified or referenced? [Clarity, Spec §FR-005]

## Requirement Consistency
- [x] CHK010 Do success metrics (SC-001..SC-005) align with the performance and behavior stated in Functional Requirements (e.g., p95 timings, exclusion rules)? [Consistency, Spec §SC-001..SC-005 vs §FR-001..FR-014]
- [x] CHK011 Are manual review/exclusion rules consistent between low-confidence handling, sensitive content handling, and digest inclusion criteria? [Consistency, Spec §FR-004, §FR-010, §FR-013]

## Acceptance Criteria Quality / Measurability
- [x] CHK012 Can each acceptance scenario in User Stories 1–3 be tied to measurable properties in Notion (status, tags, sensitivity, confidence, citations)? [Measurability, Spec §User Stories]
- [x] CHK013 Are SC-001..SC-005 measurable with available telemetry (timestamps, counts, confidence), and is measurement method/period defined? [Measurability, Spec §SC-001..SC-005]

## Scenario Coverage
- [x] CHK014 Do requirements cover authenticated-page capture via Chrome CDP (logged-in session) in addition to clipper/share flows? [Coverage, Spec §Architecture Constraint]
- [x] CHK015 Are correction flows covered for both classification errors and summary errors, and do they specify how re-processing is triggered? [Coverage, Spec §FR-011]
- [x] CHK016 Are search/filter requirements inclusive of all key facets (tag, sensitivity, source, time range, keyword) and stated for both items and digests? [Coverage, Spec §FR-007]

## Edge Case Coverage
- [x] CHK017 Are rate-limit/backoff behaviors and visibility of pending/backlog states described for Notion API limits/downtime? [Edge Case, Spec §Edge Cases]
- [x] CHK018 Are handling rules specified for unsupported/corrupted files, very large attachments, and offline queued captures? [Edge Case, Spec §Edge Cases]
- [x] CHK019 Are duplicate/near-duplicate handling expectations stated for burst submissions across devices? [Edge Case, Spec §Edge Cases]

## Non-Functional Requirements
- [x] CHK020 Are performance targets (capture+classify p95, digest p95) tied to specific measurement points and environments (logged-in Chrome CDP)? [NFR, Spec §SC-001, §SC-003]
- [x] CHK021 Are privacy/redaction requirements for sensitive content spelled out for digests and storage (what is redacted, where stored)? [NFR, Spec §FR-013]
- [x] CHK022 Is auditability defined (backlinks, IDs) for both items and digest statements, and is the required trace format stated? [NFR/Traceability, Spec §FR-014]

## Dependencies & Assumptions
- [x] CHK023 Are external dependencies (Notion token/DB permissions, Chrome availability with user session, OpenAI key) explicitly listed with failure handling? [Dependency, Spec §Assumptions]
- [x] CHK024 Is the assumption of single-user scope and time-zone selection captured with what happens if user changes TZ later? [Assumption, Spec §Assumptions]

## Ambiguities & Conflicts
- [x] CHK025 Are rules for mixing rule-based vs LLM tagging documented, including precedence and versioning? [Ambiguity, Gap]
- [x] CHK026 Is there guidance on when to exclude items permanently vs temporarily (pending/ready/excluded states) and how that affects digests? [Ambiguity, Spec §FR-004, §FR-010, §FR-013]
