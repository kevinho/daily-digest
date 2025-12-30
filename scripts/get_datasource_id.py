#!/usr/bin/env python3
"""
获取 Notion 同步数据库的 Data Source ID

用法:
    python scripts/get_datasource_id.py --database-id YOUR_DATABASE_ID

或者设置环境变量后直接运行:
    python scripts/get_datasource_id.py
"""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def get_database_info(database_id: str, token: str) -> dict:
    """Query Notion API for database information."""
    import httpx
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
    }
    
    url = f"https://api.notion.com/v1/databases/{database_id}"
    
    with httpx.Client() as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def find_data_source_id(database_id: str, token: str) -> str | None:
    """
    尝试通过多种方式获取 Data Source ID。
    
    对于同步数据库，Data Source ID 通常与 Database ID 相同。
    """
    import httpx
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    
    # 方法1: 直接尝试用 database_id 作为 data_source_id 查询
    test_url = f"https://api.notion.com/v1/data_sources/{database_id}/query"
    
    with httpx.Client() as client:
        try:
            resp = client.post(test_url, headers=headers, json={})
            if resp.status_code == 200:
                return database_id
        except Exception:
            pass
    
    return None


def main():
    parser = argparse.ArgumentParser(description="获取 Notion 同步数据库的 Data Source ID")
    parser.add_argument(
        "--database-id",
        default=os.getenv("NOTION_DATABASE_ID"),
        help="Notion 数据库 ID（默认从 NOTION_DATABASE_ID 环境变量读取）",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("NOTION_TOKEN"),
        help="Notion Integration Token（默认从 NOTION_TOKEN 环境变量读取）",
    )
    args = parser.parse_args()
    
    if not args.database_id:
        print("❌ 请提供 --database-id 或设置 NOTION_DATABASE_ID 环境变量")
        sys.exit(1)
    
    if not args.token:
        print("❌ 请提供 --token 或设置 NOTION_TOKEN 环境变量")
        sys.exit(1)
    
    print(f"📊 查询数据库: {args.database_id}")
    print("-" * 50)
    
    try:
        # 获取数据库基本信息
        db_info = get_database_info(args.database_id, args.token)
        
        print(f"📝 数据库标题: {db_info.get('title', [{}])[0].get('plain_text', 'N/A')}")
        print(f"📁 Parent 类型: {db_info.get('parent', {}).get('type', 'N/A')}")
        
        # 检查是否为同步数据库
        is_synced = db_info.get("is_inline", False) is False and db_info.get("parent", {}).get("type") == "block_id"
        
        if is_synced:
            print("🔗 这是一个同步数据库")
        else:
            print("📄 这是一个普通数据库")
        
        print("-" * 50)
        
        # 尝试获取 Data Source ID
        ds_id = find_data_source_id(args.database_id, args.token)
        
        if ds_id:
            print(f"✅ Data Source ID: {ds_id}")
            print()
            print("将以下内容添加到 .env 文件:")
            print(f"  NOTION_DATA_SOURCE_ID={ds_id}")
        else:
            print("ℹ️  未找到 Data Source ID（可能是普通数据库，无需配置）")
            print()
            print("如果确定是同步数据库，可尝试:")
            print(f"  NOTION_DATA_SOURCE_ID={args.database_id}")
            
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

