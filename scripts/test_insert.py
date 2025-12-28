#!/usr/bin/env python3
"""
Test Insert: 强行插入一条数据，验证数据库是否可用
"""
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
client = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = os.getenv("NOTION_DATABASE_ID")

def test_insert():
    print(f"🧪 正在尝试向数据库 {db_id} 插入测试数据...")
    
    try:
        new_page = client.pages.create(
            parent={"database_id": db_id},
            properties={
                "Name": {
                    "title": [{"text": {"content": "Test Entry from Python"}}]
                },
                "URL": {
                    "url": "https://www.google.com"
                },
                "Status": {
                    "select": {"name": "To Read"} 
                },
                "Summary": {
                    "rich_text": [{"text": {"content": "If you see this, the system works!"}}]
                }
            }
        )
        print("\n✅ 成功！数据已插入！")
        print(f"新页面链接: {new_page['url']}")
        print("🎉 结论：不用管 UI 怎么显示，API 是通的！可以继续开发了。")
        
    except Exception as e:
        print(f"\n❌ 插入失败: {e}")
        print("分析：如果提示 'Could not find property'，说明字段真没建成功。")

if __name__ == "__main__":
    test_insert()