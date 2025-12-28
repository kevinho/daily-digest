# Feature Specification: Personal Content Digest

**Feature Branch**: `002-content-digest`  
**Created**: 2025-12-28  
**Status**: Draft  
**Input**: User description: "构建一个信息收集/分类/摘要系统。这个系统的目的是将个人日常收集的内容进行整理和利用。设备包含手机/电脑等，使用app/浏览器等，内容包含url/文本/文件/图片等。期望通过 AI 进行整理。实现后续后续的有效利用，例如周期性的对内容进行摘要播报，例如日报，周报，月报。"

**Architecture Constraint**: Notion Database is the single source of truth for capture, classification, and digest delivery. Capture occurs by creating/updating Notion database items (via share sheet/extension/shortcut); summaries and digests are stored back into Notion pages.

**Rationale for Notion as Collection Hub**: Most target URLs require logged-in access but are accessible in desktop browsers. By clipping/sharing directly from the logged-in browser (or mobile share sheet) into Notion, we avoid storing credentials, leverage existing sessions, and keep capture + classification + summaries in one source of truth. Notion’s database/views support filtering, dedupe via canonical URL, sensitivity flags, and back-links for audit, while eliminating the need to operate our own DB and auth layer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture & Classify via Notion Inbox (Priority: P1)

The user saves links, text snippets, files, and images from phone or computer through share actions or shortcuts; each entry lands as a row/page in the Notion database with source, timestamp, and auto-tags/sensitivity labels so the user can browse a clean, organized inbox view.

**Why this priority**: Without reliable intake and classification, nothing downstream can be summarized or retrieved; this is the MVP foundation.

**Independent Test**: Share varied items (URL, text, file, image) from different devices; verify they appear in the inbox with correct metadata, tags, and confidence indicators without needing any digest features.

**Acceptance Scenarios**:

1. **Given** the user shares a URL from mobile, **When** it is sent to the system, **Then** the item shows in the inbox with the original link, capture time, device/source, preview text, and auto-tags.
2. **Given** an uploaded attachment (image/PDF), **When** processed in this phase, **Then** the system stores the file and metadata without OCR, marks it as unprocessed for text, and excludes it from digests until later support.
3. **Given** duplicate submissions of the same link, **When** processed, **Then** the system keeps one canonical entry and records duplicates as references without cluttering the inbox.

---

### User Story 2 - Scheduled Personal Digests in Notion (Priority: P2)

The user receives AI-generated digests (daily/weekly/monthly) summarizing new or updated items by topic, rendered as Notion pages with citations back to the source rows and clear action highlights.

**Why this priority**: Timely, trustworthy summaries deliver the core value of efficient absorption without manual review of every item.

**Independent Test**: With intake already working, enable schedules and verify digests are produced on time with citations and topic sections even if search/feedback features are absent.

**Acceptance Scenarios**:

1. **Given** the user schedules a weekly digest, **When** the period ends, **Then** a digest is generated within the scheduled window, grouped by topics, with citations linking to each summarized item.
2. **Given** some items are marked sensitive, **When** the digest is produced, **Then** sensitive content is redacted or summarized at a coarse level while still citing sources.
3. **Given** the user requests an ad-hoc daily digest for a custom date range, **When** generated, **Then** it includes only items from that range and notes any skipped items due to low confidence.

---

### User Story 3 - Search, Review & Corrections in Notion (Priority: P3)

The user can search/filter collected items and digests using Notion filters/views by time, source, tag, and keywords; they can correct tags or summaries directly in Notion, and corrections feed back into future outputs.

**Why this priority**: Ensures trust and ongoing quality by letting the user find items quickly and fix mistakes that inform future automation.

**Independent Test**: With intake data available, verify search/filter and correction flows work and that corrections update stored items without requiring scheduled digests to operate.

**Acceptance Scenarios**:

1. **Given** the user searches by tag and date, **When** results are shown, **Then** they include original items with lineage, confidence, and sensitivity indicators, plus links back to the originating source.
2. **Given** the user flags a wrong tag or summary sentence, **When** they submit a correction, **Then** the item updates, future digests use the corrected data, and the correction is recorded for learning.
3. **Given** a low-confidence item in the inbox, **When** the user chooses to review later, **Then** it remains queued with reminders and is excluded from digests until resolved.


### Edge Cases

- Duplicate or near-duplicate links/files submitted across devices in a short window; Notion dedupe via canonical URL field.
- Unsupported or corrupted files/images/PDFs; user notified with reason; attachments preserved but marked unprocessed (no OCR in this phase).
- Offline capture from mobile queued and retried when online; preserves original timestamp/source and backfills into Notion.
- Very large files or images exceeding limits; system should reject gracefully and suggest alternatives.
- Notion API rate limits or downtime; retries with backoff and visibility of pending items.
- Low-confidence classification or summarization; items held for manual review and excluded from digests until confirmed.
- Sensitive content requiring redaction before sharing in digests; ensure lineage is retained while details are masked.
- Time zone differences between devices; schedules and digest ranges must respect the user’s configured time zone.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Capture MUST occur by creating Notion database entries from phone and computer (share sheet, browser extension/shortcut), including URL/text/file/image, with source, device, timestamp, and item type properties.
- **FR-002**: System MUST normalize captured items when text/HTML is available; PDF/image OCR is out-of-scope for this phase—such items MUST be stored with an “unprocessed” marker and excluded from digests.
- **FR-003**: System MUST auto-classify items with topic tags and sensitivity labels stored as Notion properties, including confidence scores and the rule/prompt version used.
- **FR-004**: Items with low confidence MUST be marked in Notion and excluded from digest queries until confirmed or corrected.
- **FR-005**: System MUST deduplicate by canonical URL/content hash, linking duplicates to a single Notion entry while keeping source references.
- **FR-006**: Users MUST be able to edit tags, sensitivity, and notes directly in Notion; edits MUST update downstream digests and search immediately.
- **FR-007**: Users MUST be able to search/filter via Notion views/filters by keyword, tag, sensitivity, source, and time range, and open the original source from results.
- **FR-008**: System MUST generate scheduled digests (daily, weekly, monthly) from Notion entries in the window, grouped by topic, and publish as Notion pages with citations to each entry.
- **FR-009**: Users MUST be able to request on-demand digests for a custom date range or topic focus, with the same citation and grouping rules as scheduled digests.
- **FR-010**: Summaries MUST include scope (time window), citations to Notion entry links, confidence indicators, and highlight items awaiting review or excluded due to sensitivity.
- **FR-011**: Feedback/corrections MUST be captured in Notion (properties or comments) and applied to future digests and classifications.
- **FR-012**: Notifications MUST inform users when digests are ready or when items require review; notifications must respect user-configured quiet hours (Notion mentions/email acceptable).
- **FR-013**: Privacy controls MUST be enforced via sensitivity properties: mark private/sensitive items, exclude them from shared digests, and support deletion with confirmation, reflecting in Notion.
- **FR-014**: Auditability MUST rely on Notion backlinks: every digest sentence references entry IDs/links for traceability.

### Key Entities *(include if feature involves data)*

- **Content Item**: Raw artifact (URL/text/file/image), normalized text, source/device, capture time, type, tags, sensitivity, confidence, canonical reference for duplicates, status (pending/ready/excluded).
- **Source/Channel**: Device or app used for capture; includes user identity, consent state, and channel (mobile app, browser extension, desktop uploader).
- **Taxonomy Tag**: Controlled topic labels and sensitivity levels with versions; includes descriptions and examples.
- **Digest**: Time window, topic sections, included item IDs, summary statements with citations and confidence, generation time, schedule or ad-hoc indicator.
- **Feedback/Correction**: Target item or digest section, issue type (tag error, summary error, sensitivity error), user note, resolution status, and applied changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of captured items appear in the Notion inbox with metadata and initial classification within 10 seconds p95 of user submission.
- **SC-002**: At least 90% of captured items reach digests without requiring manual review; low-confidence queue remains below 10% of weekly items.
- **SC-003**: Scheduled digests are delivered within the configured window (e.g., daily/weekly/monthly) with 100% of summary points carrying citations to Notion entries.
- **SC-004**: User-rated usefulness of digests averages ≥4.0/5 after two weeks of use; fewer than 5% of digest items are reported as inaccurate.
- **SC-005**: Privacy actions (delete or mark-sensitive) are reflected in Notion and excluded from outputs within 24 hours, with confirmation to the user.

### Assumptions

- Notion Database is the authoritative store; no additional DB is introduced.
- Single primary user account; multi-user sharing is out of scope for this feature.
- User provides a preferred time zone for scheduling; if absent, device time zone at first setup is used.
- Notion API token and required workspace permissions are available.
- Default language support assumed for the user’s primary language; multilingual OCR/text may require later enhancement.
