# Tasks: Digest 内容呈现优化

**Branch**: `008-digest-presentation` | **Date**: 2025-12-30  
**Spec**: specs/008-digest-presentation/spec.md | **Plan**: specs/008-digest-presentation/plan.md

## US1 - 综合概述快速阅读 (P1)

**Goal**: 生成 100-150 字的综合概述，30 秒内可阅读理解批次主题。

### Tasks

- [ ] **T001**: 在 `src/llm.py` 实现 `generate_overview(items)` 函数，使用 AI 生成综合概述
- [ ] **T002**: 实现 `generate_overview_fallback(items)` 降级方案，无 AI 时简单拼接标签和数量
- [ ] **T003**: 修改 `src/digest.py` 的 `build_digest()` 函数，调用 `generate_overview()` 生成概述

**Independent Test**: 生成 Digest 后验证顶部有综合概述，长度 100-150 字。

---

## US2 - 分条目摘要浏览 (P1)

**Goal**: 每个条目显示结构化摘要：标题 + Highlights (3-5条) + URL。

### Tasks

- [ ] **T004**: 在 `src/llm.py` 实现 `parse_highlights(insights)` 函数，解析 highlights 列表
- [ ] **T005**: 修改 `build_digest()` 输出结构，每个条目包含 title、highlights、url
- [ ] **T006**: 在 `src/notion.py` 添加 block 生成辅助函数：`_heading1/2/3`、`_bullet`、`_divider`、`_link`

**Independent Test**: 验证每个条目显示标题、3-5 条 highlights（每条 ≤30 字）、可点击 URL。

---

## US3 - 按标签分组浏览 (P2)

**Goal**: 分条目摘要按标签分组显示，每组有明确标题。

### Tasks

- [ ] **T007**: 修改 `build_digest()` 输出 `tag_groups` 结构（替换原 `sections`）
- [ ] **T008**: 更新 `create_digest_page()` 使用新结构渲染 Notion 页面

**Independent Test**: 验证条目按标签分组，多标签条目在各组中都出现。

---

## 集成与测试

### Tasks

- [ ] **T009**: 更新 `main.py` 适配新的 `build_digest()` 返回结构
- [ ] **T010**: 创建 `tests/test_digest.py` 测试 digest 构建逻辑
- [ ] **T011**: 创建 `tests/test_llm_overview.py` 测试综合概述生成（含降级）

---

## MVP / Incremental Strategy

| 阶段 | 任务 | 可验证结果 |
|------|------|------------|
| Phase 1 | T001-T003 | 综合概述生成并显示 |
| Phase 2 | T004-T006 | 分条目摘要结构化 |
| Phase 3 | T007-T008 | 标签分组显示 |
| Phase 4 | T009-T011 | 集成与测试 |

---

## Progress Tracking

| Task | Status | Notes |
|------|--------|-------|
| T001 | ✅ | `generate_overview()` in llm.py |
| T002 | ✅ | `generate_overview_fallback()` in llm.py |
| T003 | ✅ | `build_digest()` calls overview |
| T004 | ✅ | `parse_highlights()` in llm.py |
| T005 | ✅ | New tag_groups structure |
| T006 | ✅ | Block helpers in notion.py |
| T007 | ✅ | Merged with T008 |
| T008 | ✅ | `create_digest_page()` updated |
| T009 | ✅ | main.py adapted |
| T010 | ✅ | tests/test_digest.py |
| T011 | ✅ | tests/test_llm_overview.py |

