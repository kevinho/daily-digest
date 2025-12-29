import os
import re
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Ensure .env is loaded even when llm is imported standalone; tolerate permission issues
try:
    load_dotenv()
except PermissionError:
    pass


def _get_openai_client():
    """Get OpenAI client if available, None otherwise."""
    api_key = os.getenv("OPENAI_API_KEY")
    # Clean any proxy envs that might be injected by shell/tools
    for k in [
        "OPENAI_PROXY",
        "OPENAI_HTTP_PROXY",
        "OPENAI_HTTPS_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ]:
        os.environ.pop(k, None)

    try:
        import openai  # type: ignore

        openai.proxy = None
        openai.proxies = None
        from openai import OpenAI as _OpenAI  # type: ignore

        class OpenAI(_OpenAI):  # type: ignore
            def __init__(self, *args, **kwargs):
                kwargs.pop("proxies", None)
                kwargs.pop("proxy", None)
                super().__init__(*args, **kwargs)

    except ImportError:
        return None

    if not api_key:
        return None
    
    return OpenAI(api_key=api_key)


def generate_overview(items: List[Dict]) -> str:
    """
    Generate a comprehensive overview for a batch of items (100-150 chars).
    
    Args:
        items: List of items, each with title, summary/tldr, tags
        
    Returns:
        Overview text (100-150 Chinese characters)
    """
    if not items:
        return "本批次无内容。"
    
    client = _get_openai_client()
    if client:
        try:
            # Build content summary for prompt
            content_lines = []
            for item in items[:20]:  # Limit to 20 items
                tags = item.get("tags", ["未分类"])
                tag = tags[0] if tags else "未分类"
                title = item.get("title", "无标题")
                summary = (item.get("summary") or item.get("tldr") or "")[:100]
                content_lines.append(f"- [{tag}] {title}: {summary}")
            
            content_summary = "\n".join(content_lines)
            
            prompt = f"""请为以下{len(items)}条内容生成一段综合概述（100-150字）。
要求：
1. 概括主要主题类别和数量分布
2. 提炼核心要点和亮点
3. 使用中文，简洁明了

内容列表：
{content_summary}

请直接输出概述内容，不要添加标题或前缀。"""

            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            content = resp.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            print(f"OpenAI error in generate_overview: {e}")
    
    # Fallback to simple overview
    return generate_overview_fallback(items)


def generate_overview_fallback(items: List[Dict]) -> str:
    """
    Generate a simple overview without AI.
    
    Args:
        items: List of items
        
    Returns:
        Simple overview text
    """
    if not items:
        return "本批次无内容。"
    
    # Count by tag
    tag_counts: Dict[str, int] = {}
    for item in items:
        tags = item.get("tags", ["未分类"])
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Build overview
    total = len(items)
    tag_parts = []
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        tag_parts.append(f"{tag}（{count}条）")
    
    tags_str = "、".join(tag_parts[:5])  # Top 5 tags
    
    # Get first few titles as highlights
    highlights = []
    for item in items[:3]:
        title = item.get("title", "")
        if title:
            highlights.append(title[:20])
    
    highlights_str = "、".join(highlights) if highlights else ""
    
    overview = f"本批次共收集{total}条内容，涵盖{tags_str}。"
    if highlights_str:
        overview += f"重点内容包括：{highlights_str}等。"
    
    return overview[:200]  # Limit length


def parse_highlights(insights: str) -> List[str]:
    """
    Parse insights text into a list of highlights.
    
    Args:
        insights: Raw insights text (may contain bullet points)
        
    Returns:
        List of highlight strings (3-5 items, each ≤30 chars)
    """
    if not insights:
        return []
    
    # Split by newlines and clean up
    lines = insights.strip().split("\n")
    highlights = []
    
    for line in lines:
        # Remove bullet markers
        line = line.strip()
        line = re.sub(r"^[-•*·]\s*", "", line)
        line = re.sub(r"^\d+[.、]\s*", "", line)  # Remove numbered list markers
        line = line.strip()
        
        if not line:
            continue
        
        # Remove common prefixes like "Insights:" or "要点:"
        line = re.sub(r"^(Insights|要点|TLDR|总结)[：:]\s*", "", line, flags=re.IGNORECASE)
        line = line.strip()
        
        if not line:
            continue
        
        # Truncate to 30 chars if needed
        if len(line) > 30:
            line = line[:30]
        
        highlights.append(line)
        
        if len(highlights) >= 5:
            break
    
    return highlights[:5]  # Max 5 highlights


def generate_digest(text: str) -> Dict[str, str]:
    """
    Summarize text with OpenAI if available; otherwise fall back to truncate.
    """
    client = _get_openai_client()
    
    if client:
        try:
            prompt = (
                "请用中文总结下面内容，输出两部分：\n"
                "TLDR: 一句话总结\n"
                "Insights: 列出3-5条要点，每条不超过30字。\n\n"
                f"内容:\n{text[:8000]}"
            )
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            content = resp.choices[0].message.content or ""
            # 简单切分：第一行 TLDR，其余为 insights
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            tldr = lines[0] if lines else content[:200]
            insights = "\n".join(lines[1:]) if len(lines) > 1 else "- " + tldr
            return {"tldr": tldr, "insights": insights}
        except Exception as e:
            print(f"OpenAI error: {e}")
    
    # Fallback
    tldr = (text or "TL;DR placeholder")[:120]
    # Try to create simple bullet insights from sentences
    sentences = re.split(r"[。！？!?\.]\s*", text or "")
    insights_list = []
    for s in sentences:
        s = s.strip()
        if s:
            insights_list.append(f"- {s[:80]}")
        if len(insights_list) >= 3:
            break
    insights = "\n".join(insights_list) if insights_list else "- " + tldr
    return {
        "tldr": tldr,
        "insights": insights,
    }


def classify(text: str) -> Dict[str, any]:
    """Stub classifier; replace with rule+LLM hybrid."""
    return {
        "tags": ["general"],
        "sensitivity": "public",
        "confidence": 0.8,
        "rule_version": "rule-v0",
        "prompt_version": "prompt-v0",
    }


def summarize_sections(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Produce lightweight section summaries with citations.
    Each item should have: id, title, summary (tldr), tags.
    """
    sections: List[Dict[str, str]] = []
    for item in items:
        title = item.get("title") or item.get("id", "item")
        tldr = item.get("summary") or item.get("tldr") or ""
        sections.append(
            {
                "title": title,
                "summary": tldr[:500],
                "citations": [item.get("id")],
                "tags": item.get("tags", []),
            }
        )
    return sections


# ============================================================
# Digest Generation Functions for Reporting System
# ============================================================

def generate_daily_digest(items: List[Dict]) -> Dict[str, any]:
    """
    Generate a daily digest from inbox items.
    
    Args:
        items: List of items with title, summary, tags
        
    Returns:
        Dict with 'overview', 'highlights', 'categories'
    """
    if not items:
        return {
            "overview": "今日无新增内容。",
            "highlights": [],
            "categories": {},
        }
    
    client = _get_openai_client()
    if client:
        try:
            # Build content summary
            content_lines = []
            for item in items[:30]:  # Limit items
                title = item.get("title", "无标题")
                tags = item.get("tags", ["未分类"])
                summary = (item.get("summary") or "")[:100]
                content_lines.append(f"- [{', '.join(tags[:2])}] {title}: {summary}")
            
            content_summary = "\n".join(content_lines)
            
            prompt = f"""你是一个知识管理助手。请根据以下今日收集的{len(items)}条内容摘要，生成一份"今日知识地图"：

{content_summary}

请按以下JSON格式输出（不要添加```json标记）：
{{
    "overview": "今日知识收获总结（100-150字）",
    "highlights": ["重点内容1", "重点内容2", "重点内容3"],
    "hot_topics": ["热门话题1", "热门话题2"]
}}"""

            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )
            content = resp.choices[0].message.content or "{}"
            # Clean up markdown formatting if present
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            
            import json
            result = json.loads(content)
            return {
                "overview": result.get("overview", ""),
                "highlights": result.get("highlights", []),
                "categories": {},
            }
        except Exception as e:
            print(f"OpenAI error in generate_daily_digest: {e}")
    
    # Fallback
    return _daily_digest_fallback(items)


def _daily_digest_fallback(items: List[Dict]) -> Dict[str, any]:
    """Fallback daily digest without AI."""
    # Count tags
    tag_counts: Dict[str, int] = {}
    for item in items:
        for tag in item.get("tags", ["未分类"]):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Build overview
    total = len(items)
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]
    tag_str = "、".join(f"{t}（{c}条）" for t, c in top_tags)
    overview = f"今日共收集{total}条内容，涵盖{tag_str}。"
    
    # Extract highlights (top 3-5 titles)
    highlights = [item.get("title", "")[:30] for item in items[:5] if item.get("title")]
    
    return {
        "overview": overview,
        "highlights": highlights,
        "categories": {},
    }


def generate_weekly_digest(daily_reports: List[Dict]) -> Dict[str, any]:
    """
    Generate a weekly digest from daily reports.
    
    Args:
        daily_reports: List of daily report dicts with overview, highlights
        
    Returns:
        Dict with 'overview', 'trends', 'emerging', 'fading'
    """
    if not daily_reports:
        return {
            "overview": "本周无日报记录。",
            "trends": [],
            "emerging": [],
            "fading": [],
        }
    
    client = _get_openai_client()
    if client:
        try:
            # Build daily summaries
            daily_lines = []
            for report in daily_reports:
                date_str = report.get("date", "")
                overview = report.get("summary") or report.get("overview", "")
                highlights = report.get("highlights", [])
                highlights_str = "、".join(highlights[:3]) if highlights else ""
                daily_lines.append(f"- {date_str}: {overview[:100]} 要点：{highlights_str}")
            
            daily_summary = "\n".join(daily_lines)
            
            prompt = f"""你是一个知识管理助手。请根据过去一周的{len(daily_reports)}天日报总结，生成周度知识报告：

{daily_summary}

请按以下JSON格式输出（不要添加```json标记）：
{{
    "overview": "本周知识趋势总结（150-200字）",
    "trends": ["热门话题1", "热门话题2", "热门话题3"],
    "emerging": ["新兴话题1"],
    "fading": ["消失话题1"]
}}"""

            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )
            content = resp.choices[0].message.content or "{}"
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            
            import json
            result = json.loads(content)
            return {
                "overview": result.get("overview", ""),
                "trends": result.get("trends", []),
                "emerging": result.get("emerging", []),
                "fading": result.get("fading", []),
            }
        except Exception as e:
            print(f"OpenAI error in generate_weekly_digest: {e}")
    
    # Fallback
    return _weekly_digest_fallback(daily_reports)


def _weekly_digest_fallback(daily_reports: List[Dict]) -> Dict[str, any]:
    """Fallback weekly digest without AI."""
    count = len(daily_reports)
    
    # Aggregate all highlights
    all_highlights = []
    for report in daily_reports:
        all_highlights.extend(report.get("highlights", []))
    
    overview = f"本周共{count}天有内容记录。"
    
    return {
        "overview": overview,
        "trends": all_highlights[:5],
        "emerging": [],
        "fading": [],
    }


def generate_monthly_digest(weekly_reports: List[Dict]) -> Dict[str, any]:
    """
    Generate a monthly digest from weekly reports.
    
    Args:
        weekly_reports: List of weekly report dicts
        
    Returns:
        Dict with 'overview', 'dominant_themes', 'evolution'
    """
    if not weekly_reports:
        return {
            "overview": "本月无周报记录。",
            "dominant_themes": [],
            "evolution": "",
        }
    
    client = _get_openai_client()
    if client:
        try:
            # Build weekly summaries
            weekly_lines = []
            for report in weekly_reports:
                title = report.get("title", "")
                overview = report.get("summary") or report.get("overview", "")
                trends = report.get("highlights", [])
                trends_str = "、".join(trends[:3]) if trends else ""
                weekly_lines.append(f"- {title}: {overview[:100]} 趋势：{trends_str}")
            
            weekly_summary = "\n".join(weekly_lines)
            
            prompt = f"""你是一个知识管理助手。请根据本月的{len(weekly_reports)}个周报总结，生成月度知识回顾：

{weekly_summary}

请按以下JSON格式输出（不要添加```json标记）：
{{
    "overview": "本月知识获取高层次总结（200-250字）",
    "dominant_themes": ["主导主题1", "主导主题2"],
    "evolution": "话题演变描述（从月初到月末的变化）"
}}"""

            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3,
            )
            content = resp.choices[0].message.content or "{}"
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```\w*\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            
            import json
            result = json.loads(content)
            return {
                "overview": result.get("overview", ""),
                "dominant_themes": result.get("dominant_themes", []),
                "evolution": result.get("evolution", ""),
            }
        except Exception as e:
            print(f"OpenAI error in generate_monthly_digest: {e}")
    
    # Fallback
    return _monthly_digest_fallback(weekly_reports)


def _monthly_digest_fallback(weekly_reports: List[Dict]) -> Dict[str, any]:
    """Fallback monthly digest without AI."""
    count = len(weekly_reports)
    
    # Aggregate themes
    all_themes = []
    for report in weekly_reports:
        all_themes.extend(report.get("highlights", []))
    
    overview = f"本月共{count}周有内容记录。"
    
    return {
        "overview": overview,
        "dominant_themes": all_themes[:5],
        "evolution": "",
    }
