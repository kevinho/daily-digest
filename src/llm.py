import os
from typing import Dict, List, Tuple, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


def generate_digest(text: str) -> Dict[str, str]:
    """
    Summarize text with OpenAI if available; otherwise fall back to truncate.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
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
        except Exception:
            pass

    # Fallback
    return {
        "tldr": (text or "TL;DR placeholder")[:200],
        "insights": "- Key points will appear here.",
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
