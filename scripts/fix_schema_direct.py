#!/usr/bin/env python3
"""
Direct Schema Fixer (Configurable API Version)
通过 .env 配置 API 版本，解决 Data Source 兼容性问题。
"""
import os
import sys
import json
from dotenv import load_dotenv
from notion_client import Client, APIResponseError

# 1. 加载配置
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
TARGET_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID")  # 从「Manage data sources -> Copy data source ID」拿

# 获取版本号，默认兜底为 2022-06-28 (经典版)
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")

if not NOTION_TOKEN or not TARGET_DATABASE_ID:
    print("❌ 错误: 请检查 .env 文件中的 TOKEN 和 DATABASE_ID")
    sys.exit(1)
if not DATA_SOURCE_ID:
    print("❌ 错误: 缺少 NOTION_DATA_SOURCE_ID（在 Manage data sources -> Copy data source ID 获取）")
    sys.exit(1)

# ==============================================================================
# 🔑 Client 初始化
# 从环境变量读取版本号，实现解耦
# ==============================================================================
client = Client(
    auth=NOTION_TOKEN,
    notion_version=NOTION_VERSION
)


def update_schema(updates: dict):
    body = {
        "properties": updates,  # 就是你原来构造的 updates
    }
    client.request(
        path=f"data_sources/{DATA_SOURCE_ID}",
        method="patch",
        body=body,
    )

def fix_database_schema():
    print(f"⚙️  配置加载完毕:")
    print(f"   - Database ID: {TARGET_DATABASE_ID}")
    print(f"   - API Version: {NOTION_VERSION} (关键参数)")
    
    print(f"\n🔄 正在连接数据库...")
    
    try:
        # 1. 获取现状
        db = client.databases.retrieve(database_id=TARGET_DATABASE_ID)
        
        # 检查是否成功获取到了 properties (只有旧版API或者非Data Source才会有)
        if "properties" in db:
            print(f"✅ 连接成功！读取到现有字段: {list(db['properties'].keys())}")
        else:
            print("❌ 警告：未读取到 Properties。")
            print(f"   可能原因：当前 API 版本 ({NOTION_VERSION}) 强制返回 Data Source 格式。")
            print("   建议：请确保 .env 中 NOTION_VERSION=2022-06-28")
            return

        current_props = db['properties']
        updates = {}

        # 2. 准备更新 (字段定义)
        # ---------------------------------------------------------
        
        # Status (Select)
        if "Status" not in current_props:
            print("➕ 准备创建: Status (Select)")
            updates["Status"] = {
                "select": {
                    "options": [
                        {"name": "To Read", "color": "blue"},
                        {"name": "Pending", "color": "yellow"},
                        {"name": "Done", "color": "green"},
                        {"name": "Error", "color": "red"}
                    ]
                }
            }

        # Summary
        if "Summary" not in current_props:
            print("➕ 准备创建: Summary (Rich Text)")
            updates["Summary"] = {"rich_text": {}}

        # URL
        if "URL" not in current_props:
            print("➕ 准备创建: URL")
            updates["URL"] = {"url": {}}

        # Tags
        if "Tags" not in current_props:
            print("➕ 准备创建: Tags")
            updates["Tags"] = {"multi_select": {}}
            
        # Confidence
        if "Confidence" not in current_props:
            print("➕ 准备创建: Confidence")
            updates["Confidence"] = {"number": {"format": "number"}}

        # ---------------------------------------------------------

        # 3. 执行更新
        if not updates:
            print("\n✨ 数据库 Schema 已是最新，无需更新。")
        else:
            print(f"\n🚀 正在提交更新 ({len(updates)} 个字段)...")
            update_schema(updates)
            print("✅ 更新成功！（data_sources patch）所有字段已就绪。")


    except APIResponseError as e:
        print(f"\n❌ API 请求失败: {e.code}")
        print(f"   消息: {e.message}")

if __name__ == "__main__":
    fix_database_schema()