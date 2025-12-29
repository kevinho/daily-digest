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
