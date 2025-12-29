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

- [ ] T001 [P] 添加 `TWITTER_SCREENSHOT_ENABLE` 配置到 `src/utils.py`
- [ ] T002 [P] 添加 `TWITTER_SCREENSHOT_ENABLE=true` 到 `.env.example`
- [ ] T003 创建临时目录 `tmp/` 并添加到 `.gitignore`

---

## Phase 2: User Story 1 - 自动截取 Tweet 截图 (Priority: P1) 🎯 MVP

**Goal**: 处理 Twitter URL 时自动截取推文截图并保存到 Notion Files 字段

**Independent Test**: 处理一条 Tweet 后，检查 Notion 条目的 Files 字段是否包含截图文件

### Implementation for User Story 1

- [ ] T010 [US1] 实现 `capture_tweet_screenshot()` 函数在 `src/browser.py`
  - 优先截取 `article[data-testid="tweet"]` 元素
  - 回退到可见区域截图
  - 文件名格式 `tweet-{id}.png`
  - 返回文件路径或 None

- [ ] T011 [US1] 实现 `upload_file_to_item()` 方法在 `src/notion.py`
  - 研究 Notion `/v1/files` API 上传方案
  - 如不可行，回退到外部 URL 或本地路径记录

- [ ] T012 [US1] 集成截图功能到 `main.py` 的 `process_item()` 函数
  - 检查 `TWITTER_SCREENSHOT_ENABLE` 配置
  - 在 Twitter 内容提取后调用截图
  - 上传成功后清理临时文件

- [ ] T013 [US1] 添加截图相关测试到 `tests/test_browser.py`
  - 测试元素截图成功场景
  - 测试回退到页面截图场景

**Checkpoint**: 此时应能自动截取 Tweet 并保存到 Notion

---

## Phase 3: User Story 2 - 截图失败不影响主流程 (Priority: P2)

**Goal**: 截图失败时记录警告日志但不影响主流程处理

**Independent Test**: 模拟截图失败，验证条目仍能正常处理为 ready/pending

### Implementation for User Story 2

- [ ] T020 [US2] 在 `capture_tweet_screenshot()` 中添加完善的异常处理
  - 捕获所有异常并记录警告日志
  - 返回 None 而非抛出异常

- [ ] T021 [US2] 在 `main.py` 中处理截图失败场景
  - 截图返回 None 时跳过上传
  - 可选：在 Reason 字段记录 "截图失败" 注释
  - 确保状态仍为 ready/pending

- [ ] T022 [US2] 添加错误处理测试到 `tests/test_browser.py`
  - 测试截图异常不抛出
  - 测试返回 None 时主流程继续

**Checkpoint**: 此时截图失败应不影响主流程

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: 文档更新和最终验证

- [ ] T030 [P] 更新 `specs/006-twitter-screenshot/quickstart.md` 添加实际运行示例
- [ ] T031 [P] 运行全量测试确认无回归
- [ ] T032 验证端到端流程：Tweet → 截图 → Notion Files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖 - 可立即开始
- **US1 (Phase 2)**: 依赖 Setup 完成
- **US2 (Phase 3)**: 依赖 US1 完成（需要有截图功能才能测试失败场景）
- **Polish (Phase 4)**: 依赖所有用户故事完成

### Task Dependencies

```
T001, T002, T003 (并行)
       ↓
T010 → T011 → T012 → T013
                ↓
       T020 → T021 → T022
                ↓
       T030, T031 (并行) → T032
```

### Parallel Opportunities

- T001, T002, T003 可并行
- T030, T031 可并行

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup (T001-T003)
2. 完成 Phase 2: US1 核心功能 (T010-T013)
3. **验证**: 处理一条 Tweet，检查 Files 字段
4. 如果可用，即可部署 MVP

### Incremental Delivery

1. Setup → 配置就绪
2. US1 → 截图功能可用 → **MVP!**
3. US2 → 错误处理完善 → 生产就绪
4. Polish → 文档完善

---

## Notes

- Notion API 文件上传有限制，需要在 T011 中研究具体方案
- 截图文件暂存于 `tmp/` 目录，上传后删除
- 配置默认开启，可通过 `TWITTER_SCREENSHOT_ENABLE=false` 关闭
- 所有截图失败应静默处理，不影响主流程

