# Tasks: 智能条目路由

**Branch**: `007-smart-item-routing` | **Date**: 2025-12-29  
**Spec**: specs/007-smart-item-routing/spec.md | **Plan**: specs/007-smart-item-routing/plan.md

## US1 - URL 资源自动识别 (P1)

**Goal**: 有 URL 的条目自动识别为 URL_RESOURCE，执行标准抓取流程。

### Tasks

- [ ] **T001**: 创建 `src/routing.py`，定义 ItemType 枚举（URL_RESOURCE, NOTE_CONTENT, EMPTY_INVALID）
- [ ] **T002**: 实现 `classify_item(item_data, notion)` 函数，URL 非空返回 URL_RESOURCE
- [ ] **T003**: 修改 `preprocess.py`，集成 classify_item，URL_RESOURCE 走现有抓取流程

**Independent Test**: 保存带 URL 条目，验证识别为 URL_RESOURCE 并执行抓取。

---

## US2 - 纯内容笔记识别 (P1)

**Goal**: 无 URL 但有内容块的条目识别为 NOTE_CONTENT，直接标记 ready。

### Tasks

- [ ] **T004**: 在 `src/notion.py` 添加 `has_page_blocks(page_id)` 方法，使用 page_size=1 检测内容块
- [ ] **T005**: 扩展 classify_item，无 URL 时调用 has_page_blocks，有内容返回 NOTE_CONTENT
- [ ] **T006**: 在 `src/utils.py` 添加 `generate_note_name(existing_count)` 函数，格式 NOTE-YYYYMMDD-N
- [ ] **T007**: 修改 preprocess.py，NOTE_CONTENT 类型直接设置 ready 状态，使用 generate_note_name 命名

**Independent Test**: 保存纯文本条目（无 URL），验证识别为 NOTE_CONTENT 并标记 ready。

---

## US3 - 空条目识别与错误处理 (P2)

**Goal**: 既无 URL 也无内容块的空条目标记为 Error。

### Tasks

- [ ] **T008**: 扩展 classify_item，无 URL 且无内容块返回 EMPTY_INVALID
- [ ] **T009**: 修改 preprocess.py，EMPTY_INVALID 类型调用 mark_as_error 并记录 Reason

**Independent Test**: 保存空条目，验证识别为 EMPTY_INVALID 并标记 Error。

---

## 测试与验证

### Tasks

- [ ] **T010**: 创建 `tests/test_routing.py`，测试 ItemType 枚举和 classify_item 函数
- [ ] **T011**: 扩展 `tests/test_preprocess.py`，测试路由集成逻辑

---

## MVP / Incremental Strategy

| 阶段 | 任务 | 可验证结果 |
|------|------|------------|
| Phase 1 | T001-T003 | URL_RESOURCE 识别并抓取 |
| Phase 2 | T004-T007 | NOTE_CONTENT 识别并标记 ready |
| Phase 3 | T008-T009 | EMPTY_INVALID 标记 Error |
| Phase 4 | T010-T011 | 测试覆盖 |

---

## Progress Tracking

| Task | Status | Notes |
|------|--------|-------|
| T001 | ⬜ | |
| T002 | ⬜ | |
| T003 | ⬜ | |
| T004 | ⬜ | |
| T005 | ⬜ | |
| T006 | ⬜ | |
| T007 | ⬜ | |
| T008 | ⬜ | |
| T009 | ⬜ | |
| T010 | ⬜ | |
| T011 | ⬜ | |

