#!/usr/bin/env python3
"""
Check Notion database/data source schema against required fields.

Usage:
  python scripts/check_schema.py
Requires env:
  NOTION_TOKEN (required)
  NOTION_DATABASE_ID (required unless NOTION_DATA_SOURCE_ID is set)
  NOTION_DATA_SOURCE_ID (optional, preferred if using synced DB)
"""
import sys
from typing import Dict, Optional

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

load_dotenv()


def fetch_properties(client: Client, data_source_id: Optional[str], database_id: Optional[str]) -> Dict:
    if data_source_id:
        try:
            return client.request(path=f"data_sources/{data_source_id}", method="get").get("properties", {})
        except APIResponseError as exc:
            print(f"[warn] data_source fetch failed: {exc}", file=sys.stderr)
    if not database_id:
        raise RuntimeError("Missing NOTION_DATABASE_ID")
    return client.databases.retrieve(database_id).get("properties", {})


def main() -> int:
    import os

    token = os.getenv("NOTION_TOKEN")
    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")
    database_id = os.getenv("NOTION_DATABASE_ID")
    if not token:
        print("Missing NOTION_TOKEN", file=sys.stderr)
        return 1
    if not data_source_id and not database_id:
        print("Missing NOTION_DATABASE_ID (or NOTION_DATA_SOURCE_ID)", file=sys.stderr)
        return 1

    client = Client(auth=token)
    props = fetch_properties(client, data_source_id, database_id)

    # Required properties and accepted types
    required = {
        "Name": {"title"},
        "URL": {"url"},
        "Raw Content": {"rich_text"},
        "Status": {"status", "select"},  # accept either
        "Summary": {"rich_text"},
        "Confidence": {"number"},
        "Sensitivity": {"select"},
        "Files": {"files"},
        "Canonical URL": {"url"},
        "Duplicate Of": {"relation"},
        "Tags": {"multi_select"},
        "Rule Version": {"rich_text"},
        "Prompt Version": {"rich_text"},
        "Reason": {"rich_text"},  # audit/notes now mandatory
    }

    found = {}
    for name, meta in props.items():
        if isinstance(meta, dict) and "type" in meta:
            found[name] = meta["type"]

    missing = []
    type_mismatch = []
    for name, allowed_types in required.items():
        if name not in found:
            missing.append(name)
        elif found[name] not in allowed_types:
            type_mismatch.append((name, found[name], allowed_types))

    print("=== Notion properties detected ===")
    for name, ptype in sorted(found.items()):
        print(f"- {name}: {ptype}")

    if missing or type_mismatch:
        print("\n[FAIL] Schema issues:")
        if missing:
            print(f"- Missing required: {', '.join(missing)}")
        if type_mismatch:
            for name, got, allowed in type_mismatch:
                print(f"- Type mismatch: {name} is {got}, expected one of {sorted(allowed)}")
        status = 1
    else:
        print("\n[PASS] All required properties present with acceptable types.")
        status = 0

    return status


if __name__ == "__main__":
    sys.exit(main())

