# Quickstart: 修复 Twitter 内容获取 (005-fix-twitter-content)

## 核心改进

### Hybrid 提取策略

Twitter 内容提取现采用两阶段策略：

1. **Priority 1 - Meta Tags (即时)**
   - 从 `<link type="application/json+oembed" title="...">` 提取完整推文内容
   - 从 `<meta property="og:title">` 提取标题
   - 无需等待 DOM 加载，速度更快

2. **Priority 2 - DOM (回退)**
   - 仅当 Meta 内容不足时等待 DOM
   - 使用 `div[data-testid="tweetText"]` 选择器
   - 配置化等待时间

### 页面缓存

- 同一 URL 只打开一次
- 标题和正文同时缓存
- 避免重复网络请求

## 前置条件

1. 配置 `.env`：
   ```
   NOTION_TOKEN=...
   NOTION_ITEM_DB_ID=...
   CHROME_REMOTE_URL=http://localhost:9222
   
   # Twitter 专用配置（可选）
   TWITTER_WAIT_MS=10000        # Twitter 页面等待时间，默认 10s
   PAGE_FETCH_RETRIES=1         # 正文抓取重试次数，默认 1
   PAGE_TITLE_RETRIES=1         # 标题抓取重试次数，默认 1
   ```

2. 启动调试 Chrome（需已登录 Twitter）：
   ```bash
   ./start_chrome.sh
   ```

3. 确认端口监听：
   ```bash
   curl http://127.0.0.1:9222/json/version
   ```

## 运行

```bash
source .venv/bin/activate
python main.py --digest daily
```

## 调试

如果 Tweet 提取失败，使用调试脚本：

```bash
python scripts/debug_twitter_content.py \
  --url "https://x.com/user/status/123456" \
  --cdp "http://localhost:9222" \
  --screenshot debug_screenshot.png \
  --html debug_dump.html
```

检查输出：
- `tweetText locator count: N` — N>0 说明 DOM 元素存在
- 截图和 HTML 可用于定位问题

## 预期行为

| 场景 | 预期结果 |
|------|----------|
| 正常 Tweet | 从 Meta 即时提取，Raw Content 有内容 |
| 复杂 Tweet | Meta 不足时等待 DOM 加载 |
| 登录墙/阻断 | Status=Error，Reason 说明原因 |
| 重复 URL | 从缓存读取，不重新打开页面 |

## 提取策略详解

```
┌─────────────────────────────────────────────────────┐
│                  fetch_page_content                  │
├─────────────────────────────────────────────────────┤
│  1. Check cache → return if hit                     │
│  2. Navigate to URL                                 │
│  3. Get HTML                                        │
│  4. If Twitter:                                     │
│     ├─ Try _extract_twitter_meta(html)              │
│     │   └─ Parse oembed title + og:title            │
│     ├─ If text < 10 chars:                          │
│     │   └─ Wait + _extract_twitter_dom(page)        │
│     └─ Cache both title + text                      │
│  5. Else: trafilatura                               │
└─────────────────────────────────────────────────────┘
```

## 排查

- **blocked: login/JS wall detected**: 确认调试 Chrome 已登录 Twitter
- **Meta 无内容**: 页面可能需要更长等待，增加 `TWITTER_WAIT_MS`
- **标题为空**: 检查 og:title 是否存在
- **DOM 提取失败**: 检查 `tweetText` 元素是否被 Shadow DOM 包裹

