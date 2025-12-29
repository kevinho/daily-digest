# Quickstart: Twitter 内容读取 (003-twitter-ingest)

## 前置
- 准备 `.env`：`NOTION_TOKEN`, `NOTION_DATABASE_ID/NOTION_DATA_SOURCE_ID`, `CHROME_REMOTE_URL`（若用已登录 Chrome），`LOG_LEVEL` 等。
- Notion 字段包含 `Reason`（rich_text）；可运行 `python scripts/check_schema.py` 验证。
- 确保有可用的登录状态：  
  - 方案 A：使用已启动的调试 Chrome（`start_chrome.sh` 或手动 `--remote-debugging-port=9222`）。  
  - 方案 B：Playwright 启动浏览器时带反爬参数（见反爬示例）。

## 反爬/浏览器参数示例（Playwright）
在 `src/browser.py` 配置入口中可参考（Python 伪代码）：
```
launch args:
  headless=False
  args=[
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
  ]
context:
  user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
  viewport={"width":1280,"height":720}
  device_scale_factor=2
  has_touch=False
  is_mobile=False
  locale="en-US"
  timezone_id="America/Los_Angeles"
init_script:
  navigator.webdriver = undefined
  navigator.plugins   = [1,2,3,4,5]
```

## 运行
1) 安装依赖（首次）：`pip install -r requirements.txt`  
2) 校验 Notion schema：`python scripts/check_schema.py`  
3) 启动/确认调试浏览器可用（端口 9222 或 `.env` 中的 `CHROME_REMOTE_URL`）  
4) 执行抓取（按主流程在 main.py 中集成后）：  
```
python main.py --digest daily   # 如已集成 twitter 处理路径，抓取队列中 tweet URL
```
（若提供专用入口，可改为 `python main.py --twitter <url>`，以实际实现为准）

## 预期行为
- 合法 tweet：抓取正文写入 Raw Content，Status=ready/pending，Reason 为空或写入来源信息，Canonical URL 去重。  
- 阻断/登录墙/无效 URL：Status=Error，Reason 记录具体原因，不写错误正文。  
- 插件来源（save to notion）：与基础抓取字段一致，来源标记为插件。  
- 幂等：重复运行不会重复写入已 ready/pending 的同一 Canonical URL，失败项可在条件满足后重试。

## 故障排查
- 抓取结果为空/阻断：确认浏览器已登录、端口/URL 正确；检查反爬参数是否生效。  
- Notion 更新失败：检查 token/DB ID/字段名（Reason 必须存在）。  
- 重复写入：检查 Canonical URL 归一化逻辑是否启用。  

