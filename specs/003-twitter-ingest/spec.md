# Feature Specification: Twitter 内容读取

**Feature Branch**: `003-twitter-ingest`  
**Created**: 2025-12-29  
**Status**: Draft  
**Input**: "Twitter 内容读取：1) 基础抓取，需解决反爬/合法浏览器（CDP 接入）。2) 深度抓取，参考 save to notion Chrome 插件的技术原理。"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - 基础抓取（合法浏览器/CDP） (Priority: P1)

在已登录、合法的桌面浏览器/CDP 会话中，抓取指定 tweet/X 页面正文并写入 Notion，规避反爬与登录墙。

**Why this priority**: 基础抓取是后续所有自动化和插件集成的前提。

**Independent Test**: 提供一条可访问的 tweet 链接，运行抓取，验证正文、Canonical URL、状态写入 Notion，且遇到阻断时报错不写入错误正文。

**Acceptance Scenarios**:

1. **Given** 已登录 CDP 浏览器，**When** 抓取一条可访问 tweet，**Then** 正文写入 Notion，状态为 ready/pending，记录 Canonical URL。
2. **Given** 返回登录墙/JS 阻断页，**When** 抓取，**Then** 状态标记 Error，Reason 说明阻断原因，不写入错误正文。

---

### User Story 2 - 插件深度抓取（参考 save to notion） (Priority: P1)

对 save to notion 插件保存的 Twitter 条目进行抓取与深度补全，保持字段一致，并标记来源。

**Why this priority**: 插件是常用入口，需要与基础抓取同等质量和字段。

**Independent Test**: 用插件保存一条 tweet 到 Notion，运行处理，验证正文/URL/状态/Reason/来源写入并与基础抓取一致。

**Acceptance Scenarios**:

1. **Given** 插件保存的 Twitter 条目，**When** 处理，**Then** 抓取正文并更新 Notion 必需字段，来源标记为插件。
2. **Given** 插件保存但 URL 无效/被阻断，**When** 处理，**Then** 状态 Error，Reason 说明问题，不写入错误正文。

---

### User Story 3 - 幂等与重复防护 (Priority: P2)

多次运行抓取时，不重复写入成功项；失败项可在条件满足后重试成功；避免重复/冲突。

**Why this priority**: 保证数据质量和可运营性，避免污染 Notion。

**Independent Test**: 对同一 tweet 连续运行，验证成功项不重复，失败项在登录恢复后可成功更新状态。

**Acceptance Scenarios**:

1. **Given** 已成功抓取的 tweet，**When** 再次运行，**Then** 不重复写入正文/摘要，状态保持 ready/pending。
2. **Given** 之前因阻断失败的 tweet，**When** 登录恢复后重试，**Then** 抓取成功并更新状态为 ready/pending。

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

- 未登录或登录过期导致登录墙/JS 阻断页。  
- tweet 被删除、私有或区域限制；短链无法解析到 tweet。  
- 插件保存的项缺 URL 或 URL 与正文不符。  
- 同一 tweet 多次保存/处理的重复去重。  
- 网络超时或 CDP 会话失效，需要可重试。

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: 系统 MUST 在已登录的合法浏览器/CDP 会话中抓取 Twitter/X 正文，检测并阻断 JS/登录墙/反爬页；阻断时标记 Error 并写 Reason，不写入错误正文。  
- **FR-002**: 系统 MUST 支持处理 save to notion 插件保存的 Twitter 条目，抓取正文并写入与基础抓取一致的字段；标记来源（插件/手动）。  
- **FR-003**: 系统 MUST 校验输入 URL 是 tweet 链接；无法解析或无效时标记 Error，避免错误写入。  
- **FR-004**: 系统 MUST 写入 Notion 必需字段：Name/标题、URL、Raw Content、Summary/备注（含错误原因）、Status、Reason（必填）、Canonical URL、Duplicate Of、Tags、Rule Version、Prompt Version，保持幂等。  
- **FR-005**: 系统 MUST 处理失败/阻断时记录原因；成功抓取时根据置信度更新状态为 ready 或 pending。  
- **FR-006**: 系统 MUST 支持重试/重跑的幂等性：同一 tweet 多次运行不重复写入，失败项在条件满足后可重试成功。  
- **FR-007**: 系统 SHOULD 提供手动触发及插件触发后的统一处理入口，复用同一抓取逻辑。  
- **FR-008**: 系统 SHOULD 记录抓取作业日志（来源、耗时、结果）以便排查。  

### Key Entities

- **Tweet Item**: Name、URL、Raw Content、Status、Reason、Canonical URL、Tags、Summary 等。  
- **Capture Job**: 抓取动作及结果（成功/错误、来源、耗时）。  

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: ≥90% 的可访问 tweet 在已登录状态下一次抓取成功。  
- **SC-002**: 100% 的阻断/无效链接被标记 Error 并写入 Reason，不产生错误正文。  
- **SC-003**: 重跑同一 tweet 不产生重复内容或错误覆盖，重复率 0。  
- **SC-004**: 插件保存的 Twitter 项处理后字段齐备（URL/正文/状态/Reason），与基础抓取一致。  
