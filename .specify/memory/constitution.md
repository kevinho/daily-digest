<!--
Sync Impact Report
Version: 0.0.0 → 1.0.0
Modified principles: populated from template (new)
Added sections: Core Principles, Operational Constraints, Workflow & Quality, Governance (populated)
Removed sections: none
Templates requiring updates: .specify/templates/plan-template.md ✅ (no change needed), .specify/templates/spec-template.md ✅, .specify/templates/tasks-template.md ✅, .specify/templates/agent-file-template.md ✅, .specify/templates/checklist-template.md ✅
Follow-up TODOs: TODO(RATIFICATION_DATE): set the original adoption date
-->

# Daily Digest Constitution

## Core Principles

### I. Trustworthy Intake & Consent
All ingested items MUST include source provenance (who, where, when) and a clear usage
intent; unverified or disallowed sources are rejected, not queued. User consent and
opt-out signals MUST be honored before storage, sharing, or model usage. Rationale:
data quality and ethics depend on transparent, permitted inputs.

### II. Structured Capture Before Processing
Every captured item MUST conform to a declared schema: raw content, normalized text,
timestamp, author/source, topic tags, sensitivity, and confidence. Auto-tagging MUST
store confidence and rules used; low-confidence items are routed to manual triage.
Taxonomies and tagging rules MUST be versioned to keep summaries reproducible.

### III. Privacy, Security, and Least Access
Personally identifiable or sensitive content MUST be minimized at intake, encrypted in
transit and at rest, and redacted before external sharing. Access is role-scoped with
auditable logs; secrets are never embedded in prompts or outputs. Retention windows and
deletion paths MUST be defined per sensitivity class.

### IV. Summarization Quality and Traceability
Every summary MUST cite source references (IDs or links) and declare scope and
assumptions. Quality checks MUST include factual consistency, coverage of key points,
and freshness. Summaries with low confidence or missing citations MUST be blocked until
reviewed. Automated evaluators are calibrated with human-reviewed benchmarks.

### V. Feedback Loops and Safe Automation
Automations (classification, summarization, routing) MUST expose their decision traces
and confidence. Users can correct outputs; corrections feed back into evaluation sets
and model prompts/config. On automation failure or low confidence, the system falls
back to manual review with clear to-do surfaces and notifications.

## Operational Constraints

- Data flows MUST preserve lineage from raw intake → normalized content → classified
  entries → summaries, with IDs traceable across stages.
- Supported formats MUST include text and standard HTML pages. PDF/images OCR is
  out-of-scope for the current phase; such files MUST be stored as attachments and
  explicitly marked as unprocessed. Unsupported formats are rejected with actionable
  errors.
- Performance: ingestion and classification MUST meet p95 ≤ 5s for single items;
  summarization batches MUST meet p95 ≤ 60s. Where unmet, backlog handling MUST avoid
  data loss and surface queue status until recovered.
- Evaluation assets (taxonomies, benchmarks, redaction rules) MUST be versioned and
  change-managed.

## Workflow & Quality Gates

- Intake pipeline MUST validate schema, sensitivity, and consent before storage.
- Classification changes (taxonomy or rules) MUST include migration notes and backfill
  plans for existing items.
- Summaries MUST pass automated checks (citation presence, length bounds, forbidden
  phrase filters) and, for sensitive items, human review before publication.
- Definition of Done for changes: updated tests or evaluation cases, updated taxonomy/
  rule docs, and monitoring dashboards/alerts for the affected stage.

## Governance

- Constitution compliance is a mandatory review item for all changes; reviewers MUST
  block merges that violate principles or gates.
- Amendments require: written proposal, impact review on data, evaluations, and
  operations, plus an update to downstream templates if needed.
- Versioning follows SemVer for this constitution; last amended date updates on every
  approved change. Material principle additions/removals bump MINOR; incompatible
  redefinitions bump MAJOR; wording clarifications bump PATCH.
- Incident handling: any data leak, consent violation, or inaccurate summary leading to
  user impact MUST trigger a postmortem and remediation tasks tracked to closure.
- Runtime guidance lives in feature plans/specs; this constitution supersedes other
  process docs where conflicts arise.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): set once adoption date is chosen | **Last Amended**: 2025-12-28
