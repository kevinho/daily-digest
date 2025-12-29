# Feature Specification: 智能条目路由

**Feature Branch**: `007-smart-item-routing`  
**Created**: 2025-12-29  
**Status**: Draft  
**Input**: 实现智能路由逻辑，区分 URL 资源和内容笔记

## User Scenarios & Testing *(mandatory)*

### User Story 1 - URL 资源自动识别 (Priority: P1)

用户保存一个包含 URL 的条目到 Notion，系统自动识别为 URL_RESOURCE 类型，并执行标准的内容抓取和摘要流程。

**Why this priority**: URL 资源是最常见的收集类型，需要优先保证其处理正确。

**Independent Test**: 保存一个带 URL 的条目，验证系统识别为 URL_RESOURCE 并执行抓取流程。

**Acceptance Scenarios**:

1. **Given** 条目的 URL 字段有有效链接，**When** 系统处理该条目，**Then** 自动识别为 URL_RESOURCE 类型。
2. **Given** URL_RESOURCE 类型条目，**When** 标题缺失，**Then** 从 URL 页面获取标题回填。
3. **Given** URL_RESOURCE 类型条目，**When** 处理完成，**Then** 执行分类和摘要流程。

---

### User Story 2 - 纯内容笔记识别 (Priority: P1)

用户保存一个没有 URL 但有内容块（文本/图片）的条目，系统识别为 NOTE_CONTENT 类型，跳过抓取，直接标记为 ready，命名规则为 NOTE-日期-序号。

**Why this priority**: 支持快速笔记和图片剪辑是核心需求。

**Independent Test**: 保存一个只有文本内容无 URL 的条目，验证识别为 NOTE_CONTENT 并直接标记 ready。

**Acceptance Scenarios**:

1. **Given** 条目 URL 字段为空但有内容块，**When** 系统处理，**Then** 识别为 NOTE_CONTENT 类型。
2. **Given** NOTE_CONTENT 类型条目，**When** 处理完成，**Then** 状态直接设为 ready（不做 summary）。
3. **Given** NOTE_CONTENT 类型条目无标题，**When** 系统命名，**Then** 使用格式 "NOTE-YYYYMMDD-序号"。

---

### User Story 3 - 空条目识别与错误处理 (Priority: P2)

用户保存一个既无 URL 也无内容块的空条目，系统识别为 EMPTY_INVALID 类型，标记为 Error 状态。

**Why this priority**: 防止无效条目污染数据库。

**Independent Test**: 保存一个完全空的条目，验证识别为 EMPTY_INVALID 并标记 Error。

**Acceptance Scenarios**:

1. **Given** 条目 URL 为空且无内容块，**When** 系统检测，**Then** 识别为 EMPTY_INVALID 类型。
2. **Given** EMPTY_INVALID 类型条目，**When** 处理完成，**Then** 状态设为 Error，Reason 说明原因。

---

### Edge Cases

- URL 字段存在但值为空字符串：视为无 URL，检查内容块。
- 内容块只有空段落：视为无有效内容，标记 EMPTY_INVALID。
- 同一天多个 NOTE_CONTENT：序号递增（NOTE-20251229-1, NOTE-20251229-2）。
- URL 格式无效（非 http/https）：仍视为 URL_RESOURCE，后续抓取时报错。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 根据 URL 字段存在与否进行快速分类。
- **FR-002**: 系统 MUST 在 URL 为空时调用 Notion API 检查页面内容块。
- **FR-003**: 系统 MUST 使用最小 API 调用（page_size=1）检测内容块存在性。
- **FR-004**: URL_RESOURCE 类型 MUST 执行标准抓取和摘要流程。
- **FR-005**: NOTE_CONTENT 类型 MUST 直接标记 ready，不执行摘要。
- **FR-006**: NOTE_CONTENT 类型 MUST 使用 "NOTE-日期-序号" 命名规则。
- **FR-007**: EMPTY_INVALID 类型 MUST 标记为 Error 状态。
- **FR-008**: 分类结果 SHOULD 记录在 Reason 字段以便追溯。

### Key Entities

- **ItemType**: 枚举类型，包含 URL_RESOURCE、NOTE_CONTENT、EMPTY_INVALID。
- **分类结果**: 包含类型、原因、是否需要进一步处理的决策数据。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: URL 资源识别准确率 100%（URL 字段非空即识别为 URL_RESOURCE）。
- **SC-002**: 内容笔记识别准确率 ≥ 95%（有内容块但无 URL 的条目）。
- **SC-003**: 空条目 100% 被标记为 Error。
- **SC-004**: NOTE_CONTENT 处理时间 ≤ 2 秒（仅检测内容块，无抓取）。
- **SC-005**: 分类 API 调用优化：无 URL 条目每个仅调用 1 次 blocks.children.list。
