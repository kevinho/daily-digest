#!/usr/bin/env python3
"""
Direct Schema Fixer (Data Source patch version)

使用 data_sources/{id} 方式更新字段，绕过新版 API 对 databases.update 的限制。
所需环境变量：
- NOTION_TOKEN
- NOTION_DATA_SOURCE_ID  (Manage data sources -> Copy data source ID)
- NOTION_DATABASE_ID     (仅用于日志，patch 用 data_source_id)
"""
from __future__ import annotations

import os
import sys
import json
from typing import Dict

from dotenv import load_dotenv
from notion_client import Client, APIResponseError


def get_env(name: str, required: bool = False) -> str | None:
    val = os.getenv(name)
    if required and (val is None or val == ""):
        raise RuntimeError(f"Missing env: {name}")
    return val


def build_updates() -> Dict[str, Dict]:
    """Define the schema fields to ensure exist (idempotent)."""
    updates: Dict[str, Dict] = {
        # 注意：data_sources patch 不接受 status.options，保留空对象
        "Status": {"status": {}},
        "URL": {"url": {}},
        "Files": {"files": {}},
        "Summary": {"rich_text": {}},
        "Confidence": {"number": {}},
        "Sensitivity": {
            "select": {
                "options": [
                    {"name": "public"},
                    {"name": "internal"},
                    {"name": "private"},
                ]
            }
        },
        "Tags": {"multi_select": {}},
        "Canonical URL": {"url": {}},
        "Duplicate Of": {"relation": {"database_id": get_env("NOTION_DATABASE_ID") or "", "type": "single_property"}},
        "Rule Version": {"rich_text": {}},
        "Prompt Version": {"rich_text": {}},
    }
    return updates


def main() -> None:
    load_dotenv()
    token = get_env("NOTION_TOKEN", required=True)
    data_source_id = get_env("NOTION_DATA_SOURCE_ID", required=True)
    database_id = get_env("NOTION_DATABASE_ID")  # optional, for logging

    client = Client(auth=token)
    updates = build_updates()

    print("⚙️ 配置：")
    print(f"  - data_source_id: {data_source_id}")
    if database_id:
        print(f"  - database_id: {database_id} (仅日志)")

    try:
        print("\n🔄 拉取现有 schema (databases.retrieve，仅用于查看，不更新)...")
        try:
            db = client.databases.retrieve(database_id=data_source_id)
        except Exception:
            # 旧 token 权限可能不支持按 data_source_id 直接 retrieve，退回使用 database_id（若可用）
            if database_id:
                db = client.databases.retrieve(database_id=database_id)
            else:
                db = {}

        props = db.get("properties") if isinstance(db, dict) else None
        if props:
            print(f"✅ 当前字段: {list(props.keys())}")
        else:
            print("ℹ️ 未能读取 properties（可能是 Data Source 只读返回或权限限制），继续以 patch 方式更新。")

        print("\n🚀 通过 data_sources patch 更新 schema...")
        result = client.request(
            path=f"data_sources/{data_source_id}",
            method="patch",
            body={"properties": updates},
        )
        print("✅ 更新完成，返回：")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except APIResponseError as e:
        print(f"\n❌ API 请求失败: {e.code}")
        print(json.dumps(e.body, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ 其他异常: {e}")
        raise


if __name__ == "__main__":
    main()