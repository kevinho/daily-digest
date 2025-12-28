#!/usr/bin/env python3
"""
Align Notion database schema for Personal Content Digest.

Requires environment variables:
- NOTION_TOKEN
- NOTION_DATABASE_ID

Optional overrides (if your column names differ):
- NOTION_PROP_STATUS, NOTION_PROP_URL, NOTION_PROP_FILES, NOTION_PROP_SUMMARY,
  NOTION_PROP_CONFIDENCE, NOTION_PROP_SENSITIVITY, NOTION_PROP_TAGS,
  NOTION_PROP_CANONICAL_URL, NOTION_PROP_DUPLICATE_OF,
  NOTION_PROP_RULE_VERSION, NOTION_PROP_PROMPT_VERSION
- NOTION_STATUS_* for status option names (pending/ready/excluded/Error/unprocessed/To Read)
"""

from __future__ import annotations

import os
from typing import Dict

from dotenv import load_dotenv
from notion_client import Client


def get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required env: {name}")
    return val


def main() -> None:
    load_dotenv()
    token = get_env("NOTION_TOKEN")
    database_id = get_env("NOTION_DATABASE_ID")

    # Property names (overridable)
    prop = {
        "status": os.getenv("NOTION_PROP_STATUS", "Status"),
        "url": os.getenv("NOTION_PROP_URL", "URL"),
        "files": os.getenv("NOTION_PROP_FILES", "Files"),
        "summary": os.getenv("NOTION_PROP_SUMMARY", "Summary"),
        "confidence": os.getenv("NOTION_PROP_CONFIDENCE", "Confidence"),
        "sensitivity": os.getenv("NOTION_PROP_SENSITIVITY", "Sensitivity"),
        "tags": os.getenv("NOTION_PROP_TAGS", "Tags"),
        "canonical_url": os.getenv("NOTION_PROP_CANONICAL_URL", "Canonical URL"),
        "duplicate_of": os.getenv("NOTION_PROP_DUPLICATE_OF", "Duplicate Of"),
        "rule_version": os.getenv("NOTION_PROP_RULE_VERSION", "Rule Version"),
        "prompt_version": os.getenv("NOTION_PROP_PROMPT_VERSION", "Prompt Version"),
    }

    # Status options (overridable)
    status_opts = {
        "pending": os.getenv("NOTION_STATUS_PENDING", "pending"),
        "ready": os.getenv("NOTION_STATUS_READY", "ready"),
        "excluded": os.getenv("NOTION_STATUS_EXCLUDED", "excluded"),
        "error": os.getenv("NOTION_STATUS_ERROR", "Error"),
        "unprocessed": os.getenv("NOTION_STATUS_UNPROCESSED", "unprocessed"),
        "to_read": os.getenv("NOTION_STATUS_TO_READ", "To Read"),
    }

    notion = Client(auth=token)

    properties: Dict[str, Dict] = {
        prop["status"]: {
            "status": {
                "options": [
                    {"name": status_opts["to_read"]},
                    {"name": status_opts["pending"]},
                    {"name": status_opts["ready"]},
                    {"name": status_opts["excluded"]},
                    {"name": status_opts["error"]},
                    {"name": status_opts["unprocessed"]},
                ]
            }
        },
        prop["url"]: {"url": {}},
        prop["files"]: {"files": {}},
        prop["summary"]: {"rich_text": {}},
        prop["confidence"]: {"number": {}},
        prop["sensitivity"]: {
            "select": {
                "options": [
                    {"name": "public"},
                    {"name": "internal"},
                    {"name": "private"},
                ]
            }
        },
        prop["tags"]: {"multi_select": {}},
        prop["canonical_url"]: {"url": {}},
        prop["duplicate_of"]: {"relation": {"database_id": database_id, "type": "single_property"}},
        prop["rule_version"]: {"rich_text": {}},
        prop["prompt_version"]: {"rich_text": {}},
    }

    result = notion.databases.update(database_id=database_id, properties=properties)
    updated_props = list(result.get("properties", {}).keys())
    print("Schema alignment requested. Properties now present:")
    for name in updated_props:
        print(f"- {name}")


if __name__ == "__main__":
    main()

