# Quickstart: Recursive Summarization System

## Concept

```
┌─────────────────────────────────────────────────────────────┐
│                  Recursive Summarization                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Level 4: Monthly ───┐                                       │
│     ↑                │ Summarizes                            │
│  Level 3: Weekly ────┤                                       │
│     ↑                │ Summarizes                            │
│  Level 2: Daily ─────┤                                       │
│     ↑                │ Summarizes                            │
│  Level 1: Items ─────┘                                       │
│                                                              │
│  Key Principle: Each level summarizes ONLY the level below   │
│                 (not raw data)                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Report Types

| Level | Type | Trigger | Input | Output |
|-------|------|---------|-------|--------|
| 1 | Item | Preprocessing | Raw content | Item summary |
| 2 | Daily | End of day | Today's items | Knowledge Map |
| 3 | Weekly | Sunday | 7 Daily digests | Trends & Shifts |
| 4 | Monthly | End of month | ~4 Weekly digests | High-level review |

## Database Structure

**Inbox DB** (existing):
- Contains items with summaries (Level 1)

**Reporting DB** (new):
- Type: Daily / Weekly / Monthly
- Date: Period start
- Source Reports: Links to lower-level reports
- Summary: Generated overview

## Example Flow

```
January 2025:

Items (L1)     → Daily (L2)      → Weekly (L3)        → Monthly (L4)
─────────────────────────────────────────────────────────────────────
Item 1 ─┐
Item 2 ─┼→ Daily Jan 1 ─┐
Item 3 ─┘               │
                        ├→ Weekly W1 ─┐
Item 4 ─┐               │             │
Item 5 ─┼→ Daily Jan 2 ─┤             │
        ...             │             ├→ Monthly Jan 2025
                        │             │
Daily Jan 3-7 ──────────┘             │
                                      │
Weekly W2-W4 ─────────────────────────┘
```

## Commands (MVP)

```bash
# Generate daily digest for today
python main.py digest --type daily

# Generate daily digest for specific date
python main.py digest --type daily --date 2025-01-15

# Generate weekly digest
python main.py digest --type weekly

# Generate monthly digest
python main.py digest --type monthly --month 2025-01
```

