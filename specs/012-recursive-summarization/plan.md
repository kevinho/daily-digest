# Implementation Plan: Recursive Summarization System

## Technical Context

- **Language/Version**: Python 3.11
- **Key Dependencies**: 
  - `notion-client` for Notion API
  - `openai` for AI summarization
  - Existing: `src/digest.py`, `src/notion.py`, `src/llm.py`
- **Target Platform**: macOS CLI runner

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recursive Summarization                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │ DigestService│──▶│ ReportBuilder│──▶│ ReportingDBManager   │ │
│  │ (Orchestrator)   │ (Content Gen) │   │ (Notion Write)       │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
│         │                  │                      │              │
│         ▼                  ▼                      ▼              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │ DateUtils    │   │ LLM          │   │ Notion API           │ │
│  │ (Period calc)│   │ (Summarize)  │   │ (Query/Create)       │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure Changes

```
src/
├── reporting/                    # NEW: Reporting module
│   ├── __init__.py
│   ├── models.py                 # ReportType enum, ReportData dataclass
│   ├── date_utils.py             # Date range calculations
│   ├── builder.py                # Report content builders
│   └── service.py                # DigestService orchestrator
├── notion.py                     # UPDATE: Add ReportingDBManager methods
├── digest.py                     # UPDATE: Refactor for reuse
└── llm.py                        # UPDATE: Add summarization prompts
```

## Implementation Details

### 1. Models (`src/reporting/models.py`)

```python
from enum import Enum
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

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
        if self.type == ReportType.DAILY:
            return f"Daily Digest - {self.start_date.isoformat()}"
        elif self.type == ReportType.WEEKLY:
            week_num = self.start_date.isocalendar()[1]
            return f"Weekly Digest - W{week_num:02d} {self.start_date.year}"
        else:
            return f"Monthly Digest - {self.start_date.strftime('%B %Y')}"

@dataclass
class ReportData:
    period: ReportPeriod
    overview: str
    highlights: List[str]
    source_ids: List[str]  # IDs of source reports or items
    content_blocks: List[dict]  # Notion blocks
```

### 2. Date Utilities (`src/reporting/date_utils.py`)

```python
from datetime import date, timedelta
from typing import Tuple

def get_daily_range(target_date: date) -> Tuple[date, date]:
    """Return (start, end) for a single day."""
    return (target_date, target_date)

def get_weekly_range(target_date: date) -> Tuple[date, date]:
    """Return (Monday, Sunday) for the week containing target_date."""
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return (monday, sunday)

def get_monthly_range(target_date: date) -> Tuple[date, date]:
    """Return (first day, last day) of the month."""
    first_day = target_date.replace(day=1)
    # Last day: go to next month, subtract 1 day
    if target_date.month == 12:
        last_day = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)
    return (first_day, last_day)
```

### 3. Report Builder (`src/reporting/builder.py`)

```python
class DailyReportBuilder:
    """Build daily digest from Inbox items."""
    
    def build(self, items: List[Dict]) -> ReportData:
        # Group by tags
        # Generate overview via LLM
        # Create content blocks
        pass

class WeeklyReportBuilder:
    """Build weekly digest from Daily reports."""
    
    def build(self, daily_reports: List[Dict]) -> ReportData:
        # Extract daily summaries
        # Identify trends and shifts
        # Generate week synthesis via LLM
        pass

class MonthlyReportBuilder:
    """Build monthly digest from Weekly reports."""
    
    def build(self, weekly_reports: List[Dict]) -> ReportData:
        # Extract weekly summaries
        # Track topic evolution
        # Generate month review via LLM
        pass
```

### 4. Digest Service (`src/reporting/service.py`)

```python
class DigestService:
    """Orchestrates recursive summarization."""
    
    def __init__(self, inbox_db: NotionManager, reporting_db: ReportingDBManager):
        self.inbox_db = inbox_db
        self.reporting_db = reporting_db
    
    def generate_daily(self, target_date: date) -> Optional[str]:
        """Generate daily digest for target_date."""
        # 1. Check if report already exists
        # 2. Query Inbox for items created on target_date
        # 3. Build report using DailyReportBuilder
        # 4. Create page in Reporting DB
        # 5. Return page_id
        pass
    
    def generate_weekly(self, target_date: date) -> Optional[str]:
        """Generate weekly digest for week containing target_date."""
        # 1. Check if report already exists
        # 2. Query Reporting DB for Daily reports in week
        # 3. Build report using WeeklyReportBuilder
        # 4. Create page in Reporting DB with relations to dailies
        pass
    
    def generate_monthly(self, target_date: date) -> Optional[str]:
        """Generate monthly digest for month containing target_date."""
        # 1. Check if report already exists
        # 2. Query Reporting DB for Weekly reports in month
        # 3. Build report using MonthlyReportBuilder
        # 4. Create page in Reporting DB with relations to weeklies
        pass
```

### 5. Notion Updates (`src/notion.py`)

Add new methods to NotionManager or create ReportingDBManager:

```python
class ReportingDBManager:
    """Manages the Reporting database for digests."""
    
    def __init__(self):
        self.database_id = get_env("NOTION_REPORTING_DB_ID")
    
    def find_report(self, report_type: str, start_date: date) -> Optional[Dict]:
        """Check if report already exists for the period."""
        pass
    
    def query_reports_in_range(
        self, 
        report_type: str, 
        start_date: date, 
        end_date: date
    ) -> List[Dict]:
        """Query reports of given type within date range."""
        pass
    
    def create_report(
        self,
        report_data: ReportData,
        source_relations: List[str],
    ) -> str:
        """Create a new report page with relations."""
        pass
```

### 6. Environment Variables

```
# Reporting DB (已配置)
NOTION_REPORTING_DB_ID=xxx    # Reporting database ID
NOTION_REPORTING_DS_ID=xxx    # Reporting datasource ID (for synced DB)

# Timezone
DIGEST_TIMEZONE=Asia/Shanghai
```

### 7. CLI Commands (`main.py`)

```python
@cli.command()
@click.option('--type', type=click.Choice(['daily', 'weekly', 'monthly']), required=True)
@click.option('--date', type=click.DateTime(formats=['%Y-%m-%d']), default=None)
def digest(type: str, date: Optional[datetime]):
    """Generate digest report."""
    target_date = date.date() if date else datetime.now().date()
    
    service = DigestService(inbox_db, reporting_db)
    
    if type == 'daily':
        page_id = service.generate_daily(target_date)
    elif type == 'weekly':
        page_id = service.generate_weekly(target_date)
    elif type == 'monthly':
        page_id = service.generate_monthly(target_date)
    
    if page_id:
        click.echo(f"Created {type} digest: {page_id}")
    else:
        click.echo(f"Failed to create {type} digest")
```

## Notion Database Schema

### Reporting DB Properties

| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Report title |
| Type | Select | Daily, Weekly, Monthly |
| Date | Date | Period start date |
| Period End | Date | Period end date |
| Source Reports | Relation | Links to lower-level reports |
| Source Items | Relation | Links to Inbox items (Daily only) |
| Summary | Text | Overview content |
| Highlights | Multi-select | Key topics/trends |
| Status | Select | draft, published |

## LLM Prompts

### Daily Synthesis Prompt

```
你是一个知识管理助手。请根据以下今日收集的内容摘要，生成一份"今日知识地图"：

{item_summaries}

要求：
1. 按主题/类别分组
2. 识别今日重点内容（3-5项）
3. 总结今日知识收获（100-150字）
```

### Weekly Trends Prompt

```
你是一个知识管理助手。请根据过去一周的每日总结，生成周度知识报告：

{daily_summaries}

要求：
1. 识别本周热门话题（出现频率最高）
2. 识别新兴话题（本周新出现）
3. 识别消失话题（本周未再出现）
4. 总结本周知识趋势（150-200字）
```

### Monthly Review Prompt

```
你是一个知识管理助手。请根据本月的周报总结，生成月度知识回顾：

{weekly_summaries}

要求：
1. 识别本月主导主题
2. 追踪话题演变（从月初到月末）
3. 生成高层次知识获取总结（200-250字）
```

## Testing Strategy

```
tests/
├── test_date_utils.py        # Date range calculations
├── test_report_builder.py    # Report content generation
├── test_digest_service.py    # Service orchestration
└── test_reporting_db.py      # Notion API interactions
```

## Rollout Plan

### Phase 1: Foundation (This PR)
- [ ] ReportType enum and ReportPeriod model
- [ ] Date utility functions
- [ ] Environment variable setup
- [ ] ReportingDBManager skeleton

### Phase 2: Daily Digest
- [ ] DailyReportBuilder implementation
- [ ] Daily digest LLM prompt
- [ ] CLI command for daily generation
- [ ] Tests for daily flow

### Phase 3: Weekly Digest
- [ ] WeeklyReportBuilder implementation
- [ ] Weekly trends LLM prompt
- [ ] CLI command for weekly generation
- [ ] Tests for weekly flow

### Phase 4: Monthly Digest
- [ ] MonthlyReportBuilder implementation
- [ ] Monthly review LLM prompt
- [ ] CLI command for monthly generation
- [ ] Tests for monthly flow

### Phase 5: Polish
- [ ] Duplicate prevention
- [ ] Missing report warnings
- [ ] Retroactive generation
- [ ] Documentation update

