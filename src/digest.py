from typing import Dict, List, Tuple

from src.llm import summarize_sections


def group_by_tag(entries: List[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for e in entries:
        tags = e.get("tags") or ["untagged"]
        for t in tags:
            grouped.setdefault(t, []).append(e)
    return grouped


def build_digest(entries: List[Dict]) -> Dict:
    """
    Build a simple digest payload from ready entries.
    Each entry should include: id, tags, summary/tldr, title.
    """
    grouped = group_by_tag(entries)
    sections: List[Dict] = []
    all_citations: List[str] = []
    for tag, items in grouped.items():
        secs = summarize_sections(items)
        for sec in secs:
            sec["title"] = f"[{tag}] {sec.get('title','')}"
            sections.append(sec)
            all_citations.extend(sec.get("citations", []))
    return {"sections": sections, "citations": list(dict.fromkeys(all_citations))}
