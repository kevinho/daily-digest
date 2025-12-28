# Data Model: Personal Content Digest (Notion)

## Entities

### Content Item (Notion DB row)
- id (Notion page id)
- title (text)
- canonical_url (url) — used for dedupe
- original_url (url)
- content_type (select: url/text/file/image/pdf)
- captured_at (datetime)
- source_device (text/select: mobile/desktop)
- source_channel (text/select: clipper/share/extension)
- text_excerpt (rich text) — normalized/OCR text snippet
- attachment (file) — optional uploaded file/image/PDF
- tags (multi-select)
- sensitivity (select: public/internal/private)
- confidence (number 0-1)
- status (select: pending/ready/excluded)
- rule_version (text) — tagging rule version
- prompt_version (text) — LLM prompt/template id
- duplicate_of (relation to Content Item) — canonical reference
- notes (rich text)

### Digest (Notion page)
- id (Notion page id)
- window (text: daily/weekly/monthly or custom)
- time_range (date range)
- sections (rich text / child blocks)
- citations (links to Content Item ids)
- generated_at (datetime)
- status (select: draft/final)
- confidence (number 0-1)
- excluded_items (list of Content Item ids)

### Feedback / Correction (Notion comment or properties)
- target (relation: Content Item or Digest)
- issue_type (tag error / summary error / sensitivity error)
- user_note (rich text)
- resolved (checkbox)
- resolved_at (datetime)
- applied_change (text)

## Relationships
- Content Item -> Digest: many-to-many via citations list; Digest stores item ids and links.
- Content Item -> Content Item: duplicate_of self-reference for dedupe lineage.
- Feedback -> (Content Item | Digest): relation for corrections.

## Validation & Rules
- canonical_url unique per Content Item (reject duplicates unless marked duplicate_of).
- status transitions: pending → ready (after classification) → excluded (manual/sensitivity) or ready; excluded items never enter digests.
- low confidence (< threshold) marks status pending and excludes from digest queries until reviewed.
- sensitive = private excludes from shared digests; redaction required if summarized.
