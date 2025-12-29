# Implementation Plan: 修复 Twitter 内容获取

**Branch**: `005-fix-twitter-content` | **Date**: 2025-12-29 | **Spec**: specs/005-fix-twitter-content/spec.md

## Summary

优化 Twitter 内容获取：**Hybrid 策略**优先从 Meta Tags（oembed/og:title）即时提取内容，仅在不足时回退 DOM 等待。实现页面缓存减少重复打开。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Playwright (CDP), trafilatura, notion-client  
**Testing**: pytest  
**Target Platform**: macOS，已登录调试 Chrome  
**Performance Goals**: 单条 p95 ≤10s，成功率 ≥90%  
**Constraints**: 合法浏览器会话；阻断不写错误正文；同一 URL 只开一次

## Constitution Check

| 原则 | 合规 |
|------|------|
| I. 可信/合规 | ✅ |
| II. 结构化捕获 | ✅ |
| III. 隐私/安全 | ✅ |
| IV. 质量与可追溯 | ✅ |
| V. 反馈与安全自动化 | ✅ |

## Project Structure

```text
src/
├── browser.py        # Hybrid 提取：Meta Tags + DOM fallback
├── preprocess.py     # 标题回填
├── notion.py
└── utils.py          # 配置读取

tests/
├── test_browser.py
├── test_preprocess.py
└── test_twitter_ingest.py
```

## Key Implementation Points

### Hybrid Extraction Strategy (`src/browser.py`)

1. **`_extract_twitter_meta(html)`**: 从 HTML 解析 oembed title 和 og:title
2. **`_extract_twitter_text(page)`**: DOM 选择器 `div[data-testid="tweetText"]`
3. **`_extract_text_by_host(page, html, url)`**: 按 host 分发策略
   - Twitter: 先 Meta，不足则等待 DOM
   - 其他: trafilatura

### Page Cache

- `_PAGE_CACHE: Dict[url, {"title": str, "text": str}]`
- `fetch_page_title` / `fetch_page_content` 先查缓存

