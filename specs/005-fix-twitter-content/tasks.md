# Tasks: 修复 Twitter 内容获取

**Branch**: `005-fix-twitter-content` | **Plan**: plan.md

## Phase 1: Setup

- [X] T001: 创建功能分支和目录结构
- [X] T002: 验证现有 `.env.example` 含 `TWITTER_WAIT_MS`、`PAGE_FETCH_RETRIES`

## Phase 2: Core - Hybrid 提取器

- [X] T010: 实现 `_extract_twitter_meta(html)` - 从 oembed/og:title 提取
- [X] T011: 重构 `_extract_twitter_text(page, html)` - 先 Meta 后 DOM
- [X] T012: 更新 `_extract_text_by_host()` 使用 Hybrid 策略
- [X] T013: 确保页面缓存 `_PAGE_CACHE` 正确工作

## Phase 3: Tests

- [X] T020: 添加测试：Meta Tags 提取成功
- [X] T021: 添加测试：DOM fallback 提取
- [X] T022: 添加测试：缓存命中不重复打开

## Phase 4: Integration

- [X] T030: 集成测试：端到端 Tweet 处理
- [X] T031: 验证 `main.py` 流程无回归

## Phase 5: Polish

- [X] T040: 更新 quickstart.md
- [X] T041: 运行全量测试确认无回归

---

**Status**: ✅ All tasks completed
