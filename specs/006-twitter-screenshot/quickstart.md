# Quickstart: Twitter 页面截图 (006-twitter-screenshot)

## 功能概述

处理 Twitter 页面时自动截取推文截图，保存到 Notion 条目的 Files 字段。

## 前置条件

1. 配置 `.env`：
   ```
   # 截图功能开关（默认开启）
   TWITTER_SCREENSHOT_ENABLE=true
   ```

2. 确保 `tmp/` 目录存在（用于临时存储截图）：
   ```bash
   mkdir -p tmp
   ```

3. 启动调试 Chrome 并登录 Twitter：
   ```bash
   ./start_chrome.sh
   ```

## 运行

```bash
source .venv/bin/activate
python main.py --digest daily
```

## 预期行为

| 场景 | 预期结果 |
|------|----------|
| 正常 Tweet | 截图保存到 Files 字段，文件名 `tweet-{id}.png` |
| 截图失败 | 记录警告日志，主流程继续，状态仍为 ready/pending |
| 功能关闭 | 跳过截图，只提取文本内容 |

## 截图区域

- 优先截取 `article[data-testid="tweet"]` 元素（主推文区域）
- 如果元素不存在，回退到可见区域截图

## 配置选项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `TWITTER_SCREENSHOT_ENABLE` | `true` | 是否启用截图功能 |

## 排查

- **截图文件过大**: 推文包含多媒体时，截图可能较大，考虑压缩或降低分辨率
- **Files 字段未更新**: 检查 Notion API 权限是否包含文件上传
- **临时文件残留**: 检查 `tmp/` 目录，手动清理或增加自动清理逻辑

## 限制

- Notion API 对文件上传有限制，可能需要外部存储方案
- 截图仅保存可见区域，不支持长推文滚动截图

