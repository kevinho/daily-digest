# Quickstart: Twitter 抓取与预处理优化 (004-twitter-opt)

## 前置
- 配置 `.env`：`NOTION_TOKEN`, `NOTION_DATABASE_ID/NOTION_DATA_SOURCE_ID`, `CHROME_REMOTE_URL`（已登录调试 Chrome），`LOG_LEVEL`。  
- 确认 Notion 字段存在：Name/URL/Raw Content/Status/Reason/Source/Canonical URL 等；可运行 `python scripts/check_schema.py`。  
- 浏览器登录态：启动带 remote debugging 的 Chrome，或确保 Playwright 复用已有 context。

### 反爬/浏览器参数（env 示例）
```
ANTI_BOT_ENABLE=true
ANTI_BOT_ARGS=--disable-blink-features=AutomationControlled --no-sandbox
ANTI_BOT_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36
ANTI_BOT_VIEWPORT=1280x720
ANTI_BOT_DEVICE_SCALE=2
ANTI_BOT_LOCALE=en-US
ANTI_BOT_TIMEZONE=America/Los_Angeles
# ANTI_BOT_INIT_SCRIPT=  # 留空用默认脚本
```

## 运行
1) `pip install -r requirements.txt`  
2) `python scripts/check_schema.py`  
3) 启动调试 Chrome（或已登录的 remote-debugging 会话）  
4) 运行预处理+抓取主流程：`python main.py --digest daily` （预处理必跑，tweet 自动抓取）  

## 预期
- tweet：写入 Raw Content/Canonical/Source，阻断或无效标 Error+Reason；重复 Canonical 跳过。  
- 插件来源：Source=plugin，与手动字段一致。  
- 阻断/错误不会中断批处理；日志输出计数（success/error/duplicate/unprocessed），同时打印 `METRIC ingest_counts ...` 便于采集。
- 标题清洗：缺失或无意义（域名/URL/Untitled）会回填抓取 title，失败时用 `Bookmark:{domain}` 或附件名/`Image Clip`。

## 排查
- 阻断/无内容：确认浏览器登录态，尝试手动打开目标 tweet；检查 ANTI_BOT_* 配置；如出现 9222 连接失败，`lsof -i :9222` 或 `curl http://127.0.0.1:9222/json/version` 确认端口。  
- 反爬：尝试切换 UA/viewport/locale/timezone/init_script 或重新登录后重跑。  
- Notion 写入失败：核对 token/DB/字段名（Reason/Source/Raw Content/Canonical 必需），可先跑 `python scripts/check_schema.py`。  
- 重复写入：确认 Canonical 归一化与 Duplicate 检查生效；若需强制覆盖，先手动清理 Duplicate 关系再重试。  
- 日志示例：`Preprocess scope=pending results: {'backfilled':1,'error':0,...}`；`Ingest results: {'success':2,'error':1,...}`；`METRIC ingest_counts success=2 error=1 duplicate=0 unprocessed=0`.

