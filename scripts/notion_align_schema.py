#!/usr/bin/env python3
"""
Align Notion database schema for Personal Content Digest.
(Safe Version: Checks existing columns before updating)
"""

from __future__ import annotations

import os
import json
from typing import Dict, Any

from dotenv import load_dotenv
from notion_client import Client, APIResponseError

def get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required env: {name}")
    return val

def main() -> None:
    load_dotenv()
    token = get_env("NOTION_TOKEN")
    database_id = get_env("NOTION_DATABASE_ID")
    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")

    # 1. 定义字段映射 (Property Names)
    prop_names = {
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

    # 2. 定义状态选项 (Status Options)
    status_opts = {
        "to_read": os.getenv("NOTION_STATUS_TO_READ", "To Read"),
        "pending": os.getenv("NOTION_STATUS_PENDING", "pending"),
        "ready": os.getenv("NOTION_STATUS_READY", "ready"),
        "excluded": os.getenv("NOTION_STATUS_EXCLUDED", "excluded"),
        "error": os.getenv("NOTION_STATUS_ERROR", "Error"),
        "unprocessed": os.getenv("NOTION_STATUS_UNPROCESSED", "unprocessed"),
    }

    if not data_source_id:
        raise RuntimeError("Missing NOTION_DATA_SOURCE_ID (Manage data sources -> Copy data source ID)")

    client = Client(auth=token)
    print(f"🔄 正在连接数据库: {database_id} ...")

    try:
        # 3. 获取当前数据库 Schema，做差异对比
        current_db = client.databases.retrieve(database_id=database_id)
        current_props = current_db.get("properties", {})
        print(f"✅ 连接成功。当前包含字段: {list(current_props.keys())}")

        properties_to_update: Dict[str, Any] = {}

        # 4. 构建更新 Payload (只添加不存在的字段)

        # --- Status (使用 Select 类型以支持自定义选项) ---
        if prop_names["status"] not in current_props:
            properties_to_update[prop_names["status"]] = {
                "select": {
                    "options": [
                        {"name": status_opts["to_read"], "color": "blue"},
                        {"name": status_opts["pending"], "color": "yellow"},
                        {"name": status_opts["ready"], "color": "green"},
                        {"name": status_opts["excluded"], "color": "gray"},
                        {"name": status_opts["error"], "color": "red"},
                        {"name": status_opts["unprocessed"], "color": "default"},
                    ]
                }
            }

        # --- URL ---
        if prop_names["url"] not in current_props:
            properties_to_update[prop_names["url"]] = {"url": {}}

        # --- Files ---
        if prop_names["files"] not in current_props:
            properties_to_update[prop_names["files"]] = {"files": {}}

        # --- Summary (Rich Text) ---
        if prop_names["summary"] not in current_props:
            properties_to_update[prop_names["summary"]] = {"rich_text": {}}

        # --- Confidence (Number) ---
        if prop_names["confidence"] not in current_props:
            properties_to_update[prop_names["confidence"]] = {"number": {"format": "number"}}

        # --- Sensitivity (Select) ---
        if prop_names["sensitivity"] not in current_props:
            properties_to_update[prop_names["sensitivity"]] = {
                "select": {
                    "options": [
                        {"name": "public", "color": "green"},
                        {"name": "internal", "color": "yellow"},
                        {"name": "private", "color": "red"},
                    ]
                }
            }

        # --- Tags (Multi-Select) ---
        if prop_names["tags"] not in current_props:
            properties_to_update[prop_names["tags"]] = {"multi_select": {}}

        # --- Canonical URL ---
        if prop_names["canonical_url"] not in current_props:
            properties_to_update[prop_names["canonical_url"]] = {"url": {}}

        # --- Duplicate Of (Relation - Self Referencing) ---
        if prop_names["duplicate_of"] not in current_props:
            properties_to_update[prop_names["duplicate_of"]] = {
                "relation": {
                    "database_id": database_id,
                    "type": "dual_property",
                    "dual_property": {},
                }
            }

        # --- Versions ---
        if prop_names["rule_version"] not in current_props:
            properties_to_update[prop_names["rule_version"]] = {"rich_text": {}}

        if prop_names["prompt_version"] not in current_props:
            properties_to_update[prop_names["prompt_version"]] = {"rich_text": {}}

        # 5. 执行更新
        if not properties_to_update:
            print("✨ 数据库 Schema 已是最新，无需更新。")
        else:
            print(f"🛠 正在新增 {len(properties_to_update)} 个字段: {list(properties_to_update.keys())} ...")
            # 使用 data_sources/{id} patch 方式更新 schema，兼容新版 API
            result = client.request(
                path=f"data_sources/{data_source_id}",
                method="patch",
                body={"properties": properties_to_update},
            )
            print("✅ Schema 更新成功！（data_sources patch）")
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except APIResponseError as e:
        print(f"❌ 更新失败: {e}")
        print("提示：如果提示字段类型冲突，请先在 Notion 网页端删除该同名字段，再运行此脚本。")


if __name__ == "__main__":
    main()