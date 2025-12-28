from typing import Dict, List


def generate_digest(text: str) -> Dict[str, str]:
    # Placeholder summary structure; replace with OpenAI call later
    return {
        "tldr": text[:200] if text else "TL;DR placeholder",
        "insights": "- Insight 1\n- Insight 2",
    }


def classify(text: str) -> Dict[str, any]:
    # Placeholder classification; to be replaced by rule+LLM hybrid
    return {
        "tags": ["general"],
        "sensitivity": "public",
        "confidence": 0.8,
        "rule_version": "rule-v0",
        "prompt_version": "prompt-v0",
    }
