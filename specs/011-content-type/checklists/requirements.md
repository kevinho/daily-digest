# Requirements Checklist: ContentType Classification

## Functional Requirements

- [ ] FR-001: ContentType detected via HTTP HEAD request
- [ ] FR-002: ContentType enum covers all common MIME types
- [ ] FR-003: Platform handlers registered and dispatched correctly
- [ ] FR-004: Twitter handler with Smart Waiters
- [ ] FR-004: Generic HTML handler as fallback
- [ ] FR-006: Processing matrix followed (processable vs unprocessed)

## Edge Cases

- [ ] EC-001: Content-Type header missing → extension fallback
- [ ] EC-002: Redirect chains followed (max 5 hops)
- [ ] EC-003: Content-Type mismatch handled gracefully

## Success Metrics

- [ ] Detection accuracy > 95%
- [ ] HEAD request < 500ms average
- [ ] Twitter + Generic handlers working
- [ ] ContentType field populated for all URL items

## Non-Functional

- [ ] No breaking changes to existing flow
- [ ] All existing tests pass
- [ ] New tests for ContentType and handlers

