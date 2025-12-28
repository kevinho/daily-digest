# Contracts (Logical API / CLI)

> Delivery is via CLI/worker backed by Notion. Endpoints below describe logical commands; they may be implemented as CLI commands or minimal HTTP wrappers.

## Capture Item
- **Method**: POST /capture
- **Input**:
  - url (string, optional if raw_text present)
  - raw_text (string, optional)
  - content_type (enum: url/text/file/image/pdf)
  - attachment_url (string, optional)
  - source_device (enum: mobile/desktop)
  - source_channel (enum: clipper/share/extension)
  - captured_at (datetime)
- **Behavior**: create/update Notion entry; apply dedupe by canonical_url/hash; set status=pending; kick off normalization/classification.
- **Output**: { id, status }

## Classify Item
- **Method**: POST /classify
- **Input**: { id }
- **Behavior**: normalize text (OCR if needed), assign tags/sensitivity/confidence; set rule_version/prompt_version; status → ready or pending if low confidence.
- **Output**: { id, status, tags, sensitivity, confidence }

## Request Digest
- **Method**: POST /digest
- **Input**:
  - window (enum: daily/weekly/monthly/custom)
  - since (datetime)
  - until (datetime)
  - topics (array<string>, optional)
- **Behavior**: query Notion entries in range with status=ready; group by topic; generate summary with citations; write Notion page.
- **Output**: { digest_id, status, url }

## Feedback / Correction
- **Method**: POST /feedback
- **Input**:
  - target_id (content item or digest id)
  - issue_type (tag_error/summary_error/sensitivity_error)
  - note (string)
- **Behavior**: records feedback in Notion; adjusts downstream prompts/classifications; optional immediate re-run.
- **Output**: { recorded: true }

## Delete / Privacy Action
- **Method**: POST /privacy
- **Input**: { id, action: delete | mark_sensitive }
- **Behavior**: delete entry or set sensitivity; exclude from digests; confirm in Notion.
- **Output**: { success: true }
