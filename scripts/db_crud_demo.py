#!/usr/bin/env python3
"""
Lightweight CRUD helper for the Notion database.

Env vars:
- NOTION_TOKEN
- NOTION_DATABASE_ID
- (optional) NOTION_PROP_TITLE (default "Name")
- (optional) NOTION_PROP_STATUS (default "Status")
- (optional) NOTION_PROP_URL (default "URL")
- (optional) NOTION_PROP_SUMMARY (default "Summary")
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv
from notion_client import Client


def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing required env: {name}")
    if val is None:
        raise RuntimeError(f"Missing env and no default provided: {name}")
    return val


def build_props_config() -> Dict[str, str]:
    return {
        "title": os.getenv("NOTION_PROP_TITLE", "Name"),
        "status": os.getenv("NOTION_PROP_STATUS", "Status"),
        "url": os.getenv("NOTION_PROP_URL", "URL"),
        "summary": os.getenv("NOTION_PROP_SUMMARY", "Summary"),
    }


def query_database(client: Client, database_id: str, **body: Any) -> Dict[str, Any]:
    """Compat helper for databases query (avoids missing .query attr across versions)."""
    return client.request(
        path=f"databases/{database_id}/query",
        method="post",
        body=body,
    )


def cmd_list(client: Client, database_id: str, props: Dict[str, str], limit: int) -> None:
    resp = query_database(client, database_id, page_size=limit)
    results: List[Dict[str, Any]] = resp.get("results", [])
    print(f"Found {len(results)} items (showing up to {limit}):")
    for page in results:
        pid = page.get("id")
        pprops = page.get("properties", {})
        title_block = pprops.get(props["title"], {}).get("title", [])
        title = title_block[0]["plain_text"] if title_block else ""
        status_obj = pprops.get(props["status"], {}).get("status") or {}
        status = status_obj.get("name")
        url = pprops.get(props["url"], {}).get("url")
        print(f"- {pid} | {status} | {title} | {url}")


def cmd_create(client: Client, database_id: str, props: Dict[str, str], title: str, url: str | None, summary: str | None) -> None:
    properties: Dict[str, Any] = {
        props["title"]: {"title": [{"text": {"content": title}}]},
    }
    if url:
        properties[props["url"]] = {"url": url}
    if summary:
        properties[props["summary"]] = {"rich_text": [{"text": {"content": summary[:1900]}}]}

    page = client.pages.create(parent={"database_id": database_id}, properties=properties)
    print(f"✅ Created page: {page.get('id')}, url: {page.get('url')}")


def cmd_update_status(client: Client, props: Dict[str, str], page_id: str, status: str) -> None:
    client.pages.update(page_id=page_id, properties={props["status"]: {"status": {"name": status}}})
    print(f"✅ Updated status for {page_id} -> {status}")


def cmd_archive(client: Client, page_id: str) -> None:
    client.pages.update(page_id=page_id, archived=True)
    print(f"✅ Archived page: {page_id}")


def main() -> None:
    load_dotenv()
    token = get_env("NOTION_TOKEN", required=True)
    database_id = get_env("NOTION_DATABASE_ID", required=True)
    props = build_props_config()
    client = Client(auth=token)

    parser = argparse.ArgumentParser(description="Simple Notion DB CRUD helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List pages")
    p_list.add_argument("--limit", type=int, default=10)

    p_create = sub.add_parser("create", help="Create a page")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--url", required=False)
    p_create.add_argument("--summary", required=False)

    p_upd = sub.add_parser("update-status", help="Update status")
    p_upd.add_argument("--page-id", required=True)
    p_upd.add_argument("--status", required=True)

    p_arch = sub.add_parser("archive", help="Archive (soft-delete) a page")
    p_arch.add_argument("--page-id", required=True)

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list(client, database_id, props, args.limit)
    elif args.cmd == "create":
        cmd_create(client, database_id, props, args.title, args.url, args.summary)
    elif args.cmd == "update-status":
        cmd_update_status(client, props, args.page_id, args.status)
    elif args.cmd == "archive":
        cmd_archive(client, args.page_id)
    else:
        parser.error("Unknown command")


if __name__ == "__main__":
    main()

