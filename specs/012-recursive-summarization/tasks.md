# Implementation Tasks: Recursive Summarization System

## Overview

| Phase | Description | Tasks | Est. Time |
|-------|-------------|-------|-----------|
| Phase 1 | Foundation | T001-T007 | 2h |
| Phase 2 | Daily Digest | T008-T014 | 3h |
| Phase 3 | Weekly Digest | T015-T019 | 2h |
| Phase 4 | Monthly Digest | T020-T024 | 2h |
| Phase 5 | Polish | T025-T028 | 1h |

---

## Phase 1: Foundation ✅

### T001: Create reporting module structure ✅
**Goal**: Set up the `src/reporting/` module directory structure

**Files to create**:
- `src/reporting/__init__.py`
- `src/reporting/models.py`
- `src/reporting/date_utils.py`
- `src/reporting/builder.py`
- `src/reporting/service.py`

**Acceptance Criteria**:
- [x] All files created with proper imports in `__init__.py`
- [x] Module is importable: `from src.reporting import *`

---

### T002: Implement ReportType enum and ReportPeriod model
**Goal**: Define core data models for reports

**File**: `src/reporting/models.py`

**Implementation**:
```python
class ReportType(Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"

@dataclass
class ReportPeriod:
    type: ReportType
    start_date: date
    end_date: date
    
    @property
    def title(self) -> str:
        # Generate human-readable title
```

**Acceptance Criteria**:
- [x] `ReportType` enum with Daily, Weekly, Monthly values
- [x] `ReportPeriod` dataclass with type, start_date, end_date
- [x] `title` property generates correct titles for each type

---

### T003: Implement ReportData dataclass ✅
**Goal**: Define the data structure for report content

**File**: `src/reporting/models.py`

**Implementation**:
```python
@dataclass
class ReportData:
    period: ReportPeriod
    overview: str
    highlights: List[str]
    source_ids: List[str]
    content_blocks: List[dict]
```

**Acceptance Criteria**:
- [x] Dataclass holds all report content
- [x] Can be serialized and passed to Notion API

---

### T004: Implement date utility functions ✅
**Goal**: Create date range calculation functions

**File**: `src/reporting/date_utils.py`

**Functions**:
- `get_daily_range(target_date) -> (start, end)`
- `get_weekly_range(target_date) -> (monday, sunday)`
- `get_monthly_range(target_date) -> (first_day, last_day)`

**Acceptance Criteria**:
- [x] `get_daily_range` returns same date for start and end
- [x] `get_weekly_range` returns Monday-Sunday (ISO week)
- [x] `get_monthly_range` handles December correctly (year rollover)
- [x] All functions handle edge cases (month boundaries)

---

### T005: Write tests for date utilities ✅
**Goal**: Ensure date calculations are correct

**File**: `tests/test_date_utils.py`

**Test Cases**:
- Daily: normal date, month boundary
- Weekly: mid-week, Monday, Sunday, week spanning months
- Monthly: normal month, December, February (leap year)

**Acceptance Criteria**:
- [x] All date range calculations tested
- [x] Edge cases covered (year boundary, leap year)

---

### T006: Add environment variables for Reporting DB ✅
**Goal**: Configure Notion Reporting database connection

**Files**: `.env.example`, `src/utils.py`

**New Variables**:
```
NOTION_REPORTING_DB_ID=xxx
DIGEST_TIMEZONE=Asia/Shanghai
```

**Acceptance Criteria**:
- [x] `.env.example` updated with new variables
- [x] `get_env()` or similar can read these values
- [x] Default timezone fallback if not set

---

### T007: Create ReportingDBManager skeleton ✅
**Goal**: Set up Notion manager for Reporting database

**File**: `src/reporting/notion_reporting.py` (new)

**Methods (skeleton)**:
```python
class ReportingDBManager:
    def __init__(self, database_id: str):
        pass
    
    def find_report(self, report_type: str, start_date: date) -> Optional[Dict]:
        """Check if report exists."""
        pass
    
    def query_reports_in_range(self, report_type: str, start: date, end: date) -> List[Dict]:
        """Query reports by type and date range."""
        pass
    
    def create_report(self, report_data: ReportData, source_relations: List[str]) -> str:
        """Create new report page."""
        pass
```

**Acceptance Criteria**:
- [x] Class structure defined
- [x] Database ID loaded from environment
- [x] Method signatures defined (can be pass/NotImplemented)

---

## Phase 2: Daily Digest ✅

### T008: Implement ReportingDBManager.find_report ✅
**Goal**: Query existing reports to prevent duplicates

**File**: `src/reporting/notion_reporting.py`

**Logic**:
- Query Reporting DB with filter: Type = report_type AND Date = start_date
- Return first match or None

**Acceptance Criteria**:
- [x] Returns existing report if found
- [x] Returns None if no match
- [x] Handles API errors gracefully

---

### T009: Implement ReportingDBManager.create_report ✅
**Goal**: Create report pages in Notion

**File**: `src/reporting/notion_reporting.py`

**Logic**:
- Build properties: Name, Type, Date, Period End, Summary, Highlights
- Add relations: Source Reports or Source Items
- Create page with content blocks
- Handle 100-block limit (batch if needed)

**Acceptance Criteria**:
- [x] Creates page with correct properties
- [x] Sets relations to source items
- [x] Handles large content (>100 blocks)

---

### T010: Implement daily digest LLM prompt ✅
**Goal**: Add prompt for generating daily knowledge map

**File**: `src/llm.py`

**New Function**:
```python
def generate_daily_digest(items: List[Dict]) -> Dict[str, Any]:
    """Generate daily digest from item summaries.
    
    Returns:
        {"overview": str, "highlights": List[str], "categories": Dict}
    """
```

**Prompt**: See plan.md - Daily Synthesis Prompt

**Acceptance Criteria**:
- [x] Calls OpenAI with structured prompt
- [x] Returns overview (100-150 chars) and highlights (3-5 items)
- [x] Falls back gracefully if AI unavailable

---

### T011: Implement DailyReportBuilder ✅
**Goal**: Build daily report content from Inbox items

**File**: `src/reporting/builder.py`

**Logic**:
1. Group items by tags
2. Call `generate_daily_digest()` for overview
3. Build Notion content blocks
4. Return `ReportData`

**Acceptance Criteria**:
- [x] Groups items by tag correctly
- [x] Generates overview and highlights
- [x] Creates valid Notion blocks

---

### T012: Implement DigestService.generate_daily ✅
**Goal**: Orchestrate daily digest generation

**File**: `src/reporting/service.py`

**Logic**:
1. Calculate date range using `get_daily_range`
2. Check for existing report using `find_report`
3. Query Inbox for items created on target_date
4. Build report using `DailyReportBuilder`
5. Create page using `create_report`
6. Return page_id

**Acceptance Criteria**:
- [x] Skips if report exists (returns existing page_id)
- [x] Queries correct items from Inbox
- [x] Creates complete daily report

---

### T013: Add CLI command for daily digest ✅
**Goal**: Enable manual daily digest generation

**File**: `main.py`

**Command**:
```bash
python main.py digest --type daily [--date 2025-01-15]
```

**Acceptance Criteria**:
- [x] Command accepts `--type daily`
- [x] Optional `--date` defaults to today
- [x] Outputs page_id on success
- [x] Shows error message on failure

---

### T014: Write tests for daily digest flow ✅
**Goal**: Verify daily digest generation

**File**: `tests/test_daily_digest.py`

**Test Cases**:
- Builder correctly groups items
- Service skips existing reports
- End-to-end with mocked Notion/LLM

**Acceptance Criteria**:
- [x] DailyReportBuilder unit tests pass
- [x] DigestService integration tests pass

---

## Phase 3: Weekly Digest ✅

### T015: Implement ReportingDBManager.query_reports_in_range ✅
**Goal**: Query daily reports within a week

**File**: `src/reporting/notion_reporting.py`

**Logic**:
- Query Reporting DB: Type = "Daily" AND Date >= start AND Date <= end
- Sort by Date ascending
- Return list of report dicts

**Acceptance Criteria**:
- [x] Returns all daily reports in range
- [x] Sorted chronologically
- [x] Handles empty results

---

### T016: Implement weekly trends LLM prompt ✅
**Goal**: Generate weekly synthesis from daily summaries

**File**: `src/llm.py`

**New Function**:
```python
def generate_weekly_digest(daily_reports: List[Dict]) -> Dict[str, Any]:
    """Generate weekly digest from daily summaries.
    
    Returns:
        {"overview": str, "trends": List[str], "emerging": List[str], "fading": List[str]}
    """
```

**Acceptance Criteria**:
- [x] Identifies hot topics (frequent)
- [x] Identifies emerging topics (new this week)
- [x] Identifies fading topics (disappeared)
- [x] Generates 150-200 word overview

---

### T017: Implement WeeklyReportBuilder ✅
**Goal**: Build weekly report from daily reports

**File**: `src/reporting/builder.py`

**Logic**:
1. Extract summaries from daily reports
2. Call `generate_weekly_digest()` 
3. Build Notion blocks with trend analysis
4. Return `ReportData` with daily report IDs as sources

**Acceptance Criteria**:
- [x] Uses daily summaries, NOT raw items
- [x] Includes trend visualization
- [x] Links to daily reports

---

### T018: Implement DigestService.generate_weekly ✅
**Goal**: Orchestrate weekly digest generation

**File**: `src/reporting/service.py`

**Logic**:
1. Calculate week range using `get_weekly_range`
2. Check for existing weekly report
3. Query daily reports in range
4. Log warning if dailies missing
5. Build and create report

**Acceptance Criteria**:
- [x] Skips if weekly report exists
- [x] Warns about missing daily reports
- [x] Creates weekly with relations to dailies

---

### T019: Write tests for weekly digest flow ✅
**Goal**: Verify weekly digest generation

**File**: `tests/test_weekly_digest.py`

**Test Cases**:
- Correct date range calculation
- Handles missing daily reports
- Trend identification logic

**Acceptance Criteria**:
- [x] WeeklyReportBuilder tests pass
- [x] Service handles incomplete weeks

---

## Phase 4: Monthly Digest ✅

### T020: Implement monthly review LLM prompt ✅
**Goal**: Generate monthly knowledge review

**File**: `src/llm.py`

**New Function**:
```python
def generate_monthly_digest(weekly_reports: List[Dict]) -> Dict[str, Any]:
    """Generate monthly digest from weekly summaries.
    
    Returns:
        {"overview": str, "dominant_themes": List[str], "evolution": str}
    """
```

**Acceptance Criteria**:
- [x] Identifies dominant monthly themes
- [x] Tracks topic evolution
- [x] Generates 200-250 word overview

---

### T021: Implement MonthlyReportBuilder ✅
**Goal**: Build monthly report from weekly reports

**File**: `src/reporting/builder.py`

**Logic**:
1. Extract summaries from weekly reports
2. Call `generate_monthly_digest()`
3. Build Notion blocks with monthly review
4. Return `ReportData` with weekly report IDs as sources

**Acceptance Criteria**:
- [x] Uses weekly summaries, NOT dailies
- [x] Shows topic evolution over month
- [x] Links to weekly reports

---

### T022: Implement DigestService.generate_monthly ✅
**Goal**: Orchestrate monthly digest generation

**File**: `src/reporting/service.py`

**Logic**:
1. Calculate month range using `get_monthly_range`
2. Check for existing monthly report
3. Query weekly reports in range
4. Log warning if weeklies missing
5. Build and create report

**Acceptance Criteria**:
- [x] Skips if monthly report exists
- [x] Warns about missing weekly reports
- [x] Creates monthly with relations to weeklies

---

### T023: Add CLI commands for weekly/monthly ✅
**Goal**: Enable manual weekly/monthly digest generation

**File**: `main.py`

**Commands**:
```bash
python main.py digest --type weekly [--date 2025-01-15]
python main.py digest --type monthly [--date 2025-01-15]
```

**Acceptance Criteria**:
- [x] `--type weekly` generates for current week
- [x] `--type monthly` generates for current month
- [x] Date option targets specific period

---

### T024: Write tests for monthly digest flow ✅
**Goal**: Verify monthly digest generation

**File**: `tests/test_monthly_digest.py`

**Test Cases**:
- Month boundary handling
- Handles incomplete months
- Theme evolution tracking

**Acceptance Criteria**:
- [x] MonthlyReportBuilder tests pass
- [x] Service handles edge cases

---

## Phase 5: Polish ✅

### T025: Implement duplicate prevention ✅
**Goal**: Ensure idempotent report generation

**File**: `src/reporting/service.py`

**Logic**:
- Before creating, always check `find_report`
- Return existing page_id if found
- Log info message about skipping

**Acceptance Criteria**:
- [x] Running twice returns same page_id
- [x] No duplicate reports created
- [x] Clear logging of skip action

---

### T026: Add missing report warnings ✅
**Goal**: Alert when lower-level reports are missing

**File**: `src/reporting/service.py`

**Logic**:
- Weekly: Check if 7 dailies exist, warn about missing days
- Monthly: Check if 4-5 weeklies exist, warn about missing weeks
- Continue processing with available reports

**Acceptance Criteria**:
- [x] Warning logged for each missing report
- [x] Processing continues with partial data
- [x] Final report notes missing sources

---

### T027: Support retroactive generation ✅
**Goal**: Generate reports for past periods

**Implementation**:
- Already supported via `--date` option
- Add validation: cannot generate future reports
- Add option to force regenerate: `--force`

**Acceptance Criteria**:
- [x] Can generate reports for any past date
- [x] Rejects future dates
- [x] `--force` overwrites existing report

---

### T028: Update documentation
**Goal**: Document the new reporting system

**Files**: `README.md`, `specs/012-recursive-summarization/quickstart.md`

**Updates**:
- Add reporting commands to README
- Document Reporting DB setup
- Add example workflows

**Acceptance Criteria**:
- [ ] README includes digest commands
- [ ] Environment variables documented
- [ ] Example workflows provided

---

## Task Dependencies

```
T001 ──────────────────────────────────────────────────────┐
  │                                                         │
T002 ─┬─ T003                                               │
      │                                                     │
T004 ─┴─ T005                                               │
                                                            │
T006 ──────────────────────────────────────────────────────┤
                                                            │
T007 ─────────────────────────────────────────────────────┐│
  │                                                        ││
T008 ─┬─ T009 ────────────────────────────────────────────┤│
      │                                                    ││
T010 ─┴─ T011 ─── T012 ─── T013 ─── T014                  ││ Phase 2
                                                           ││
T015 ─── T016 ─── T017 ─── T018 ─── T019                  ││ Phase 3
                                                           ││
T020 ─── T021 ─── T022 ─── T023 ─── T024                  ││ Phase 4
                                                           ││
T025 ─── T026 ─── T027 ─── T028                           ┘│ Phase 5
                                                            │
```

## Quick Start Checklist

**Before Starting**:
- [ ] Create Notion Reporting database
- [ ] Set `NOTION_REPORTING_DB_ID` in `.env`
- [ ] Verify Inbox DB has items with summaries

**After Implementation**:
- [ ] Run `python main.py digest --type daily` 
- [ ] Verify daily report in Notion
- [ ] Run full week to test weekly
- [ ] Run full month to test monthly

