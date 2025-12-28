from typing import Dict, List, Tuple


def generate_digest(text: str) -> Dict[str, str]:
    """Stub digest summary; replace with OpenAI call."""
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
