# Implementation Plan: 智能条目路由

**Branch**: `007-smart-item-routing` | **Date**: 2025-12-29 | **Spec**: specs/007-smart-item-routing/spec.md  
**Input**: Feature specification from `/specs/007-smart-item-routing/spec.md`

## Summary

实现智能路由逻辑，根据条目的 URL 和内容块情况，将其分类为 URL_RESOURCE、NOTE_CONTENT 或 EMPTY_INVALID，并执行相应的处理流程。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: notion-client (已有)  
**Storage**: Notion Database  
**Testing**: pytest  
**Target Platform**: macOS CLI  
**Project Type**: 单仓库 Python CLI  
**Performance Goals**: NOTE_CONTENT 处理 ≤ 2s，API 调用最小化  
**Constraints**: 每个无 URL 条目最多 1 次 blocks API 调用  
**Scale/Scope**: 个人使用

## Constitution Check

| 原则 | 合规情况 |
|------|----------|
| I. 可信/合规 | ✅ 分类结果记录在 Reason 字段，可追溯 |
| II. 结构化捕获 | ✅ ItemType 枚举明确定义三种类型 |
| III. 隐私/安全 | ✅ 不涉及新的数据收集 |
| IV. 质量与可追溯 | ✅ 分类决策有明确规则 |
| V. 反馈与安全自动化 | ✅ EMPTY_INVALID 标记 Error，NOTE_CONTENT 直接 ready |

**Gate**: 通过。

## Project Structure

### Documentation (this feature)

```text
specs/007-smart-item-routing/
├── plan.md              # 本文件
├── quickstart.md        # 快速入门
├── checklists/
│   └── requirements.md  # 规格检查清单
└── tasks.md             # 任务清单
```

### Source Code (repository root)

```text
src/
├── routing.py           # 新增：ItemType 枚举和 classify_item 函数
├── notion.py            # 扩展：has_page_blocks() 方法
├── preprocess.py        # 修改：集成路由逻辑
└── utils.py             # 扩展：generate_note_name() 函数

tests/
├── test_routing.py      # 新增：路由逻辑测试
└── test_preprocess.py   # 扩展：路由集成测试
```

**Structure Decision**: 新增 `src/routing.py` 模块专门处理条目分类，保持职责单一。

## Key Implementation Points

### 1. ItemType 枚举 (`src/routing.py`)

```python
from enum import Enum

class ItemType(Enum):
    URL_RESOURCE = "url_resource"    # 有有效 URL
    NOTE_CONTENT = "note_content"    # 无 URL 但有内容块
    EMPTY_INVALID = "empty_invalid"  # 无 URL 且无内容
```

### 2. 分类函数 (`src/routing.py`)

```python
def classify_item(item_data: dict, notion: NotionManager) -> tuple[ItemType, str]:
    """
    分类条目类型。
    
    Args:
        item_data: 简化后的条目数据（含 url, id 等）
        notion: NotionManager 实例
        
    Returns:
        (ItemType, reason_string)
    """
    url = item_data.get("url", "").strip()
    page_id = item_data.get("id")
    
    # Step 1: 快速检查 URL
    if url:
        return ItemType.URL_RESOURCE, "Has valid URL"
    
    # Step 2: 检查内容块（慢，需要 API 调用）
    has_blocks = notion.has_page_blocks(page_id)
    if has_blocks:
        return ItemType.NOTE_CONTENT, "Has content blocks but no URL"
    
    return ItemType.EMPTY_INVALID, "No URL and no content blocks"
```

### 3. Notion 内容块检测 (`src/notion.py`)

```python
def has_page_blocks(self, page_id: str) -> bool:
    """
    检测页面是否有内容块。
    使用 page_size=1 最小化 API 响应。
    """
    try:
        resp = self.client.blocks.children.list(block_id=page_id, page_size=1)
        results = resp.get("results", [])
        # 过滤空段落
        for block in results:
            if block.get("type") != "paragraph":
                return True
            para = block.get("paragraph", {})
            rich_text = para.get("rich_text", [])
            if rich_text:
                return True
        return len(results) > 0 and any(...)  # 有非空内容
    except Exception:
        return False
```

### 4. NOTE 命名函数 (`src/utils.py`)

```python
def generate_note_name(existing_count: int = 0) -> str:
    """
    生成 NOTE 类型条目名称。
    格式: NOTE-YYYYMMDD-N
    """
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    return f"NOTE-{today}-{existing_count + 1}"
```

### 5. 集成到预处理 (`src/preprocess.py`)

```python
from src.routing import classify_item, ItemType

def preprocess_item(item, notion, cdp_url):
    item_type, reason = classify_item(item, notion)
    
    if item_type == ItemType.URL_RESOURCE:
        # 标准流程：抓取 + 摘要
        return process_url_resource(item, notion, cdp_url)
    
    elif item_type == ItemType.NOTE_CONTENT:
        # 直接标记 ready，命名为 NOTE-日期-序号
        name = generate_note_name()
        notion.set_title(page_id, name, note=reason)
        notion.mark_as_done(page_id, "Content note", status=notion.status.ready)
        return "note"
    
    else:  # EMPTY_INVALID
        notion.mark_as_error(page_id, reason)
        return "error"
```

## Complexity Tracking

无违宪复杂度需豁免。
