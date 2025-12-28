# Research: Personal Content Digest

## Decisions

1) Capture path (Notion + Chrome share/clipper)
- Decision: Use user-initiated share (Chrome clipper/extension or mobile share) into Notion DB; no headless login or cookie storage.
- Rationale: Logged-in browser already holds session for protected URLs; avoids handling credentials, reduces compliance risk.
- Alternatives: Headless scraping with stored cookies (rejected: higher risk, brittle), self-hosted DB intake (rejected: adds infra).

2) Deduplication & schema
- Decision: Canonical URL property + content hash; enforce unique index via checks before insert; store duplicates as references.
- Rationale: Prevent inbox clutter; maintains lineage. Notion DB can be filtered for canonical URL collisions.
- Alternatives: Heuristic text similarity only (rejected: less deterministic).

3) Classification/sensitivity
- Decision: Rule + LLM hybrid: quick rule-based tag hints (domain/URL patterns) plus LLM for summaries/tags with confidence; store versioned rule/prompt IDs.
- Rationale: Faster first-pass tagging, transparent lineage for prompts/rules.
- Alternatives: LLM-only (rejected: slower, less predictable for p95 target), rules-only (rejected: lower coverage).

4) Summarization/digests
- Decision: Use OpenAI gpt-4o for topic summaries with citations to Notion entries; batch by window (daily/weekly/monthly) and cap tokens per section.
- Rationale: Quality + speed; citations required by constitution.
- Alternatives: Local LLM (rejected: infra/quality), manual-only (rejected: reduces value).

5) Notifications
- Decision: Use Notion mentions/comments and optional email export of digest link; quiet hours observed in scheduler.
- Rationale: Stays within Notion ecosystem; no extra push infra.
- Alternatives: Custom push service (rejected: out-of-scope for single-user phase).

6) Rate limits & retries
- Decision: Notion API backoff (3 rps sustained) with jitter; queue pending operations when offline or limited; surface backlog status in quickstart/runbook.
- Rationale: Aligns with operational constraint; prevents data loss.
- Alternatives: Unlimited retries (rejected: throttling/ban risk).

## Outstanding Items
- None; current scope assumes single user and provided Notion token/DB ID.
