# Feature Specification: Twitter 抓取与预处理优化

**Feature Branch**: `004-twitter-opt`  
**Created**: 2025-12-29  
**Status**: Draft  
**Input**: "启动一个深度的优化，对于条目的清晰和 Twitter 抓取进行专项处理。预处理是启动之后必备的阶段，其中调用 Twitter 抓取逻辑。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 预处理必跑 + Twitter 抓取内置 (Priority: P1)

启动流程时，预处理阶段必须运行：校验/回填 Name 与 URL/Content，并自动对 tweet 链接调用 Twitter 抓取，写入 Notion，阻断/无效时给出明确错误。

**Why this priority**: 预处理是所有后续处理的入口，抓取内置保证数据完整、清晰。

**Independent Test**: 启动主流程，含混合条目（普通+tweet）；验证预处理运行，tweet 被抓取写入 Raw Content/Canonical/Reason/Source，阻断时标记 Error。

**Acceptance Scenarios**:
1. **Given** 待处理列表包含 tweet URL，**When** 启动流程，**Then** 预处理运行并抓取，写入正文/Canonical/Source，状态 ready/pending。
2. **Given** tweet 被登录墙/JS 阻断，**When** 预处理抓取，**Then** 状态 Error，Reason 说明阻断，流程不中断。

---

### User Story 2 - 条目清晰度提升 (Priority: P1)

抓取后条目需可追溯、可复现：记录来源（手动/插件）、Reason、Canonical、Raw Content，防止重复污染。

**Why this priority**: 提升条目可用性和审计追踪。

**Independent Test**: 对同一 tweet 多次运行，验证不重复写入；来源/Reason/Raw Content/Canonical 等字段完整；重复项被跳过或关联。

**Acceptance Scenarios**:
1. **Given** 同一 tweet 已 ready/pending，**When** 再运行，**Then** 标记 Duplicate/跳过，不重复写入。
2. **Given** 插件保存的 tweet，**When** 抓取，**Then** 写入 Source=plugin，字段与手动一致。

---

### User Story 3 - 稳定性与可恢复 (Priority: P2)

抓取阻断或失败时不影响全局流程，可重试并恢复；对环境/登录/反爬参数可配置。

**Why this priority**: 保证长时间运行的稳定性与可运维性。

**Independent Test**: 模拟阻断/失效后重跑，成功项写入，失败项可恢复；抓取参数可从配置切换。

**Acceptance Scenarios**:
1. **Given** 阻断错误，**When** 下次运行登录态恢复，**Then** 抓取成功并更新状态。  
2. **Given** 配置变更（UA/viewport/init_script），**When** 重新运行，**Then** 抓取仍能成功或给出明确错误，不崩溃。

---

### Edge Cases
- 未登录或登录过期导致登录墙/JS 阻断。  
- tweet 删除/私有/区域限制；短链无法解析。  
- 插件条目缺 URL/URL 与正文不符。  
- 同一 tweet 多次保存/处理的重复。  
- Playwright/CDP 会话失效或配置错误导致无法连接。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在预处理阶段自动调用 Twitter 抓取，对 tweet URL 写入 Raw Content/Canonical/Source/Reason/Status，阻断时标记 Error。  
- **FR-002**: 系统 MUST 记录来源（手动/插件）并在重复/已 ready/pending 的 Canonical 时跳过或关联，不重复写入。  
- **FR-003**: 系统 MUST 对阻断/无效链接给出可追溯的 Reason，不写入错误正文，流程不中断。  
- **FR-004**: 系统 SHOULD 允许通过配置（env/文件）调整反爬参数（UA/viewport/init_script/args）与 CDP 端点；配置变更无需改代码。  
- **FR-005**: 系统 MUST 支持重试与恢复：阻断后登录恢复可成功抓取；失败项可再次处理。  
- **FR-006**: 系统 MUST 保持幂等：重复运行同一 Canonical URL 不重复写入内容或摘要。  

### Key Entities

- **Item**: Name、URL、Raw Content、Summary/Reason、Status、Source、Canonical URL、Tags 等。  
- **Capture/Preprocess Job**: 抓取或预处理动作的结果（success/error/blocked、来源、耗时）。  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 预处理阶段处理的 tweet 中，≥90% 在可访问时一次抓取成功。  
- **SC-002**: 100% 阻断/无效链接标记 Error 并写 Reason，流程不中断。  
- **SC-003**: 同一 Canonical URL 重复运行不产生重复写入/摘要。  
- **SC-004**: 插件来源的 tweet 与手动来源字段一致（Raw Content/Canonical/Source/Status）。  
