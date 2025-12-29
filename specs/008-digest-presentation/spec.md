# Feature Specification: Digest 内容呈现优化

**Feature Branch**: `008-digest-presentation`  
**Created**: 2025-12-30  
**Status**: Draft  
**Input**: 优化 digest 内容呈现，结构化为综合概述+分条目摘要

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 综合概述快速阅读 (Priority: P1)

用户打开 Digest 页面，首先看到该批次所有内容的综合概述，可以在约 30 秒内快速了解本批次收集内容的整体主题和要点。

**Why this priority**: 综合概述是用户快速获取信息价值的第一入口，决定了用户是否需要深入阅读具体条目。

**Independent Test**: 生成 Digest 后，验证页面顶部显示综合概述，内容约 100-150 字，涵盖批次主要主题。

**Acceptance Scenarios**:

1. **Given** 用户有 5 条以上待处理内容，**When** 生成 Digest，**Then** 显示综合概述段落，长度约 100-150 字。
2. **Given** 综合概述已生成，**When** 用户阅读概述，**Then** 30 秒内可理解本批次内容的整体主题和核心要点。
3. **Given** 批次内容涉及多个主题，**When** 生成概述，**Then** 概述应提及主要主题类别和数量分布。

---

### User Story 2 - 分条目摘要浏览 (Priority: P1)

用户在综合概述下方看到每个条目的结构化摘要，包含标题、要点提炼和原文链接，方便按需深入阅读。

**Why this priority**: 分条目摘要是用户深入了解具体内容的主要方式，需要清晰结构化。

**Independent Test**: 验证每个条目显示标题、highlights（3-5 条要点）和可点击的 URL。

**Acceptance Scenarios**:

1. **Given** Digest 包含多个条目，**When** 查看分条目区域，**Then** 每个条目显示：标题、要点列表、URL。
2. **Given** 条目有 URL，**When** 显示条目摘要，**Then** URL 可点击跳转到原文。
3. **Given** 条目的 highlights 已生成，**When** 显示摘要，**Then** 每个 highlight 不超过 30 字，共 3-5 条。

---

### User Story 3 - 按标签分组浏览 (Priority: P2)

分条目摘要按标签（Tags）分组显示，用户可以快速定位感兴趣的主题类别。

**Why this priority**: 分组浏览提升内容发现效率，但不影响基本阅读体验。

**Independent Test**: 验证条目按标签分组，每组显示标签名称和该组条目列表。

**Acceptance Scenarios**:

1. **Given** 条目有不同标签，**When** 显示分条目区域，**Then** 按标签分组展示。
2. **Given** 某条目有多个标签，**When** 分组时，**Then** 该条目在每个相关标签组中都出现。
3. **Given** 标签组内有多个条目，**When** 显示该组，**Then** 组内条目按时间或重要性排序。

---

### Edge Cases

- 批次只有 1-2 个条目：综合概述简化，可直接列出条目主题，无需复杂归纳。
- 条目无 URL：摘要中 URL 字段显示"无链接"或省略。
- 条目无 highlights：使用 TLDR 或 Summary 字段内容替代。
- 所有条目同一标签：分组仍显示标签名，只有一个组。
- 条目无标签：归入"未分类"组。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 为每个 Digest 生成综合概述，长度约 100-150 字（约 30 秒阅读时间）。
- **FR-002**: 综合概述 MUST 涵盖批次内容的主要主题、数量分布和核心要点。
- **FR-003**: 系统 MUST 为每个条目生成结构化摘要，包含：标题、highlights、URL。
- **FR-004**: Highlights MUST 为 3-5 条要点，每条不超过 30 字。
- **FR-005**: 分条目摘要 MUST 按标签分组显示。
- **FR-006**: URL 字段 MUST 可点击跳转（在 Notion 中可点击）。
- **FR-007**: 综合概述 SHOULD 使用 AI 生成，整合所有条目内容。
- **FR-008**: 系统 SHOULD 在无 AI 可用时提供降级方案（简单拼接）。

### Key Entities

- **Digest**: 摘要汇总，包含综合概述和分条目摘要列表。
- **Overview**: 综合概述，100-150 字的整体总结。
- **ItemSummary**: 条目摘要，包含 title、highlights（列表）、url。
- **TagGroup**: 标签分组，包含标签名和该组条目摘要列表。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可在 30 秒内阅读完综合概述并理解批次内容主题。
- **SC-002**: 每个条目摘要结构完整：100% 包含标题，90% 以上包含 highlights，有 URL 的条目 100% 显示可点击链接。
- **SC-003**: 分组展示清晰：每个标签组有明确标题，组内条目按序排列。
- **SC-004**: Digest 生成时间（含 AI 调用）不超过 60 秒。
- **SC-005**: 无 AI 时降级方案可用，Digest 仍可生成（内容质量降低但结构完整）。
