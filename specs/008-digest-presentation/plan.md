# Implementation Plan: Digest 内容呈现优化

**Branch**: `008-digest-presentation` | **Date**: 2025-12-30 | **Spec**: specs/008-digest-presentation/spec.md  
**Input**: Feature specification from `/specs/008-digest-presentation/spec.md`

## Summary

优化 Digest 内容呈现结构，新增综合概述（Overview）并改进分条目摘要格式（标题+Highlights+URL），按标签分组显示。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: openai (已有)、notion-client (已有)  
**Storage**: Notion Pages  
**Testing**: pytest  
**Target Platform**: macOS CLI  
**Project Type**: 单仓库 Python CLI  
**Performance Goals**: Digest 生成 ≤ 60s（含 AI 调用）  
**Constraints**: 需支持无 AI 时的降级方案  
**Scale/Scope**: 个人使用

## Constitution Check

| 原则 | 合规情况 |
|------|----------|
| I. 可信/合规 | ✅ 不涉及新数据收集 |
| II. 结构化捕获 | ✅ 明确定义 Overview、ItemSummary、TagGroup 结构 |
| III. 隐私/安全 | ✅ 不涉及敏感数据处理变更 |
| IV. 质量与可追溯 | ✅ 保留 citations，综合概述可追溯来源 |
| V. 反馈与安全自动化 | ✅ 提供无 AI 降级方案 |

**Gate**: 通过。

## Project Structure

### Source Code Changes

```text
src/
├── llm.py               # 扩展：generate_overview() 综合概述生成
├── digest.py            # 重构：build_digest() 新结构
└── notion.py            # 扩展：create_digest_page() 新格式
```

### Key Data Structures

```python
# Digest 输出结构
{
    "overview": "综合概述文本（100-150字）",
    "tag_groups": [
        {
            "tag": "AI",
            "items": [
                {
                    "title": "条目标题",
                    "highlights": ["要点1", "要点2", "要点3"],
                    "url": "https://..."
                }
            ]
        }
    ],
    "citations": ["page_id_1", "page_id_2"]
}
```

## Key Implementation Points

### 1. 综合概述生成 (`src/llm.py`)

```python
def generate_overview(items: List[Dict]) -> str:
    """
    生成批次综合概述（100-150字）。
    
    Args:
        items: 条目列表，每个含 title, summary/tldr, tags
        
    Returns:
        综合概述文本
    """
    # 构建 prompt
    content_summary = "\n".join([
        f"- [{item.get('tags', ['未分类'])[0]}] {item.get('title')}: {item.get('summary', '')[:100]}"
        for item in items[:20]  # 限制条目数
    ])
    
    prompt = f"""请为以下{len(items)}条内容生成一段综合概述（100-150字）。
要求：
1. 概括主要主题类别和数量
2. 提炼核心要点
3. 使用中文

内容列表：
{content_summary}
"""
    # 调用 OpenAI...
```

### 2. 条目摘要结构化 (`src/llm.py`)

现有 `generate_digest()` 已返回 `tldr` 和 `insights`，需确保 highlights 格式：

```python
def parse_highlights(insights: str) -> List[str]:
    """将 insights 文本解析为 highlights 列表。"""
    lines = insights.strip().split("\n")
    highlights = []
    for line in lines:
        line = line.strip().lstrip("-•").strip()
        if line and len(line) <= 30:
            highlights.append(line)
        elif line:
            highlights.append(line[:30])  # 截断
    return highlights[:5]  # 最多5条
```

### 3. Digest 构建 (`src/digest.py`)

```python
def build_digest(entries: List[Dict]) -> Dict:
    """构建结构化 Digest。"""
    # 1. 生成综合概述
    overview = generate_overview(entries)
    
    # 2. 按标签分组
    grouped = group_by_tag(entries)
    tag_groups = []
    all_citations = []
    
    for tag, items in grouped.items():
        group_items = []
        for item in items:
            group_items.append({
                "title": item.get("title", ""),
                "highlights": parse_highlights(item.get("summary", "")),
                "url": item.get("url", ""),
            })
            all_citations.append(item.get("id"))
        tag_groups.append({"tag": tag, "items": group_items})
    
    return {
        "overview": overview,
        "tag_groups": tag_groups,
        "citations": list(dict.fromkeys(all_citations))
    }
```

### 4. Notion 页面生成 (`src/notion.py`)

```python
def create_digest_page(self, title, digest_data, metadata=None):
    children_blocks = []
    
    # 元数据
    if metadata:
        children_blocks.append(self._paragraph(f"📊 {' | '.join(f'{k}: {v}' for k, v in metadata.items())}"))
    
    # 综合概述
    children_blocks.append(self._heading1("📋 综合概述"))
    children_blocks.append(self._paragraph(digest_data.get("overview", "")))
    children_blocks.append(self._divider())
    
    # 分组条目
    for group in digest_data.get("tag_groups", []):
        children_blocks.append(self._heading2(f"【{group['tag']}】"))
        for item in group["items"]:
            # 标题
            children_blocks.append(self._heading3(f"📌 {item['title']}"))
            # Highlights（bulletlist）
            for h in item.get("highlights", []):
                children_blocks.append(self._bullet(h))
            # URL
            if item.get("url"):
                children_blocks.append(self._paragraph(f"🔗 {item['url']}"))
    
    # Citations
    children_blocks.append(self._divider())
    children_blocks.append(self._paragraph(f"引用: {', '.join(digest_data.get('citations', []))}"))
    
    return self._create_page(title, children_blocks)
```

### 5. 降级方案

无 AI 时的降级：
- 综合概述：简单拼接各标签组标题和条目数
- Highlights：从 summary 按句号切分前 3 句

## Complexity Tracking

无违宪复杂度需豁免。
