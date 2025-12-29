# Feature Spec: Recursive Summarization System

## Overview

A hierarchical reporting system that creates progressively higher-level summaries of knowledge base content. Following the structure of work reports: Item → Daily → Weekly → Monthly. Higher-level reports summarize lower-level reports, not raw data.

## User Stories

### US1: As a user, I want daily digests of my saved content
So that I can review what I captured each day in an organized format.

### US2: As a user, I want weekly summaries synthesizing my daily digests
So that I can identify patterns and trends in my interests over the week.

### US3: As a user, I want monthly reviews summarizing my weekly digests
So that I can reflect on my knowledge acquisition at a high level.

### US4: As a user, I want reports to link back to their source reports
So that I can drill down from high-level summaries to specific items.

## Functional Requirements

### FR-001: Item-Level Summarization (Level 1)
- Each item in the Inbox must have a concise `summary` field
- Summary is produced during preprocessing
- Summary captures the key insight or main point of the content

### FR-002: Daily Digest Generation (Level 2)
- **Trigger**: Manual or scheduled end-of-day execution
- **Input**: Query Inbox for items created on the target date
- **Processing**:
  - Group items by tag/category
  - Generate a "Today's Knowledge Map" overview
  - Include item count per category
  - Highlight top 3-5 items based on tags or content significance
- **Output**: 
  - Create a page in Reporting DB with Type=Daily
  - Include date in title (e.g., "Daily Digest - 2025-01-15")
  - Link to all source items via relations

### FR-003: Weekly Digest Generation (Level 3)
- **Trigger**: Manual or scheduled end-of-week execution (Sunday)
- **Input**: Query Reporting DB for Type=Daily pages within the target week
- **Processing**:
  - Synthesize the 7 daily summaries (or fewer if incomplete week)
  - Identify trends: which topics appeared most frequently
  - Identify shifts: new topics that emerged vs. topics that disappeared
  - Generate week-over-week comparison if previous week exists
- **Output**:
  - Create a page in Reporting DB with Type=Weekly
  - Include week number/date range in title (e.g., "Weekly Digest - W03 2025")
  - Link to all Daily reports via relations

### FR-004: Monthly Digest Generation (Level 4)
- **Trigger**: Manual or scheduled end-of-month execution
- **Input**: Query Reporting DB for Type=Weekly pages within the target month
- **Processing**:
  - High-level review of knowledge acquisition
  - Identify dominant themes of the month
  - Track topic evolution over the 4-5 weeks
  - Generate month-over-month comparison if previous month exists
- **Output**:
  - Create a page in Reporting DB with Type=Monthly
  - Include month/year in title (e.g., "Monthly Digest - January 2025")
  - Link to all Weekly reports via relations

### FR-005: Reporting Database Schema
- **Type**: Select field with options: Daily, Weekly, Monthly
- **Date**: Date field for the report period start
- **Period End**: Date field for the report period end
- **Source Reports**: Relation field linking to lower-level reports
- **Source Items**: Relation field linking to Inbox items (for Daily only)
- **Summary**: Rich text field for the generated overview
- **Highlights**: Multi-select for key topics/trends identified

### FR-006: Recursive Summarization Principle
- Daily digests summarize individual item summaries
- Weekly digests summarize daily digest summaries
- Monthly digests summarize weekly digest summaries
- No level should directly access data from more than one level below

## Edge Cases

### EC-001: Incomplete Periods
- Daily: Handle days with zero items (create empty digest or skip)
- Weekly: Handle weeks with fewer than 7 days (partial week at month start/end)
- Monthly: Handle months with incomplete weeks

### EC-002: Missing Lower-Level Reports
- Weekly generation with missing daily reports should proceed with available reports
- Monthly generation with missing weekly reports should proceed with available reports
- Log warnings for missing reports

### EC-003: Retroactive Generation
- Support generating reports for past dates
- Prevent duplicate reports for the same period (check before creating)

### EC-004: Timezone Handling
- All date calculations should use a consistent timezone
- Timezone should be configurable (default: user's local timezone)

## Assumptions

- Reporting DB is a separate Notion database from Inbox DB
- AI summarization is available for generating overviews
- Item summaries already exist from preprocessing (Level 1 is done)
- Users prefer consolidated reports over multiple notifications
- Standard calendar weeks (Monday-Sunday) are acceptable

## Success Criteria

| Metric | Target |
|--------|--------|
| Daily digest covers all items from the day | 100% item inclusion |
| Weekly digest references all daily digests | 100% report linkage |
| Monthly digest references all weekly digests | 100% report linkage |
| Report generation completes | < 2 minutes per report |
| Users can trace from monthly to specific item | ≤ 3 clicks |
| Digest content accurately reflects source material | User satisfaction > 80% |

## Non-Goals (This Phase)

- Real-time digest updates (reports are generated at period end)
- Custom report periods (only Daily/Weekly/Monthly)
- Export to formats other than Notion
- Automatic scheduling (manual trigger for MVP)
- Multi-user support (single user knowledge base)

