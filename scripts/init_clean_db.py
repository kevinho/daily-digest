#!/usr/bin/env python3
"""
Init Clean Database via API
彻底解决 Data Source 问题，直接通过 API 创建原生数据库。
"""
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# 1. 加载 Token
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# ⚠️⚠️⚠️ 请在这里填入你的【父页面 ID】(Parent Page ID) ⚠️⚠️⚠️
# 也就是你想把数据库放在哪个页面里？
PARENT_PAGE_ID = "2d7d3f8a9bc1806197ddc178ff221a43" 

if "请" in PARENT_PAGE_ID:
    print("❌ 错误: 请先修改脚本中的 PARENT_PAGE_ID！")
    sys.exit(1)

client = Client(auth=NOTION_TOKEN)

def create_clean_db():
    print(f"🏗 正在页面 {PARENT_PAGE_ID} 中创建原生数据库...")
    
    try:
        new_db = client.databases.create(
            parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
            title=[
                {
                    "type": "text",
                    "text": {"content": "Daily Digest (API Created)"}
                }
            ],
            properties={
                # 必须有的标题列
                "Name": {"title": {}},
                
                # 你的核心字段
                "URL": {"url": {}},
                "Summary": {"rich_text": {}},
                "Tags": {"multi_select": {}},
                "Confidence": {"number": {"format": "number"}},
                
                # 直接定义 Status 为 Select 类型
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Read", "color": "blue"},
                            {"name": "Pending", "color": "yellow"},
                            {"name": "Done", "color": "green"},
                            {"name": "Error", "color": "red"}
                        ]
                    }
                }
            }
        )
        
        print("\n" + "="*40)
        print("✅ 成功！原生数据库已诞生！")
        print("="*40)
        print(f"New Database ID: {new_db['id']}")
        print(f"New Database URL: {new_db['url']}")
        print("="*40)
        print("\n👉 下一步行动：")
        print(f"1. 复制上面的 ID: {new_db['id']}")
        print("2. 粘贴到你的 .env 文件中替换旧的 NOTION_DATABASE_ID")
        print("3. 去 Notion 页面查看，应该所有字段都齐全了！")

    except Exception as e:
        print(f"❌ 创建失败: {e}")

if __name__ == "__main__":
    create_clean_db()