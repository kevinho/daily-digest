#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion_version = os.getenv("NOTION_VERSION", "2022-06-28")
# 确保这里读到的是 .env 里那个新 ID (2d7d...21e5)
client = Client(auth=os.getenv("NOTION_TOKEN"), notion_version=notion_version)
db_id = os.getenv("NOTION_DATABASE_ID")

print(f"🕵️‍♂️ 正在验尸 ID: {db_id}")
try:
    db = client.databases.retrieve(database_id=db_id)
    # 打印核心证据
    if "properties" not in db or not db["properties"]:
        print("\n⚠️ 破案了！API 返回中没有 properties 字段。")
        print("这说明它不是一个普通数据库。完整证据如下：")
        print(json.dumps(db, indent=2, ensure_ascii=False))
    else:
        print(f"✅ 居然读到了属性: {list(db['properties'].keys())}")
except Exception as e:
    print(e)