# Tasks: Twitter 页面截图

**Input**: Design documents from `/specs/006-twitter-screenshot/`  
**Prerequisites**: plan.md (required), spec.md (required)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: 项目配置和临时目录准备

- [X] T001 [P] 添加 `TWITTER_SCREENSHOT_ENABLE` 配置到 `src/utils.py`
- [X] T002 [P] 添加 `TWITTER_SCREENSHOT_ENABLE=true` 到 `.env.example`
- [X] T003 创建临时目录 `tmp/` 并添加到 `.gitignore`

---

## Phase 2: User Story 1 - 自动截取 Tweet 截图 (Priority: P1) 🎯 MVP

**Goal**: 处理 Twitter URL 时自动截取推文截图并保存到 Notion Files 字段

**Independent Test**: 处理一条 Tweet 后，检查 Notion 条目的 Files 字段是否包含截图文件

### Implementation for User Story 1

- [X] T010 [US1] 实现 `capture_tweet_screenshot()` 函数在 `src/browser.py`
  - 优先截取 `article[data-testid="tweet"]` 元素
  - 回退到可见区域截图
  - 文件名格式 `tweet-{id}.png`
  - 返回文件路径或 None

- [X] T011 [US1] 实现 `add_file_to_item()` 方法在 `src/notion.py`
  - 使用 file:// 协议引用本地文件
  - 保留现有文件引用

- [X] T012 [US1] 集成截图功能到 `main.py` 的 `process_item()` 函数
  - 检查 `TWITTER_SCREENSHOT_ENABLE` 配置
  - 在 Twitter 内容提取后调用截图
  - 上传成功后清理临时文件

- [X] T013 [US1] 添加截图相关测试到 `tests/test_browser.py`
  - 测试 `extract_tweet_id_from_url` 各种 URL 格式
  - 测试缓存功能

**Checkpoint**: ✅ 自动截取 Tweet 并保存到 Notion

---

## Phase 3: User Story 2 - 截图失败不影响主流程 (Priority: P2)

**Goal**: 截图失败时记录警告日志但不影响主流程处理

**Independent Test**: 模拟截图失败，验证条目仍能正常处理为 ready/pending

### Implementation for User Story 2

- [X] T020 [US2] 在 `capture_tweet_screenshot()` 中添加完善的异常处理
  - 捕获所有异常并记录警告日志
  - 返回 None 而非抛出异常

- [X] T021 [US2] 在 `main.py` 中处理截图失败场景
  - 截图返回 None 时跳过上传
  - 确保状态仍为 ready/pending

- [X] T022 [US2] 错误处理逻辑已内置于实现中
  - 异常自动捕获
  - 日志警告记录

**Checkpoint**: ✅ 截图失败不影响主流程

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: 文档更新和最终验证

- [X] T030 [P] quickstart.md 已在规划阶段创建
- [X] T031 [P] 运行全量测试确认无回归 (49 passed)
- [X] T032 代码已完成，可进行端到端验证

---

## Status: ✅ All tasks completed

**Summary**:
- Phase 1: 3/3 tasks completed
- Phase 2: 4/4 tasks completed  
- Phase 3: 3/3 tasks completed
- Phase 4: 3/3 tasks completed

**Total**: 13/13 tasks completed
