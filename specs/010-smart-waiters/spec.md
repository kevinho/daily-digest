# Feature Specification: Smart Waiters for Twitter Content

**Feature Branch**: `010-smart-waiters`  
**Created**: 2025-12-30  
**Status**: Draft  
**Input**: Replace naive time.sleep(10) with deterministic wait strategy for Twitter content fetching

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 快速获取有效推文内容 (Priority: P1)

系统处理 Twitter 链接时，应尽快检测到推文内容加载完成并提取，而非固定等待 10 秒。

**Why this priority**: 减少不必要的等待时间直接提升处理效率，是本特性的核心价值。

**Independent Test**: 处理一条正常推文链接，验证系统在内容可见后立即提取，无需等待完整 10 秒。

**Acceptance Scenarios**:

1. **Given** 一条有效 Twitter 链接，**When** 页面加载推文内容，**Then** 系统在内容可见后立即提取，平均等待时间 < 5 秒。
2. **Given** 推文内容已渲染，**When** 系统检测到内容元素，**Then** 立即进入提取流程，不再等待。

---

### User Story 2 - 快速识别登录墙 (Priority: P1)

系统应在 2 秒内识别出 Twitter 登录墙，避免长时间无效等待。

**Why this priority**: 登录墙是常见阻塞场景，快速识别可显著提升失败处理效率。

**Independent Test**: 模拟登录墙场景，验证系统在 2 秒内检测到并报告错误。

**Acceptance Scenarios**:

1. **Given** Twitter 显示登录墙，**When** 系统检测页面，**Then** 2 秒内识别并标记为 "Login Wall Detected"。
2. **Given** 检测到登录墙，**When** 系统中止等待，**Then** 不再继续等待，直接返回错误状态。

---

### User Story 3 - 快速识别服务器错误 (Priority: P1)

系统应快速识别 Twitter 服务器错误页面（如 "Something went wrong"），避免无效等待。

**Why this priority**: 服务器错误是另一类常见失败场景，需要快速响应。

**Independent Test**: 模拟服务器错误页面，验证系统快速检测并报告错误。

**Acceptance Scenarios**:

1. **Given** Twitter 显示 "Something went wrong"，**When** 系统检测页面，**Then** 快速识别并标记为 "Twitter Server Error"。
2. **Given** 检测到服务器错误，**When** 系统中止等待，**Then** 返回明确的错误原因。

---

### User Story 4 - 优雅处理超时 (Priority: P2)

当推文内容在合理时间内未加载（如推文已删除），系统应优雅超时而非无限等待。

**Why this priority**: 超时处理确保系统不会卡住，但优先级略低于正常场景优化。

**Independent Test**: 处理一条已删除的推文链接，验证系统在超时后返回明确状态。

**Acceptance Scenarios**:

1. **Given** 推文已删除或不存在，**When** 等待超时，**Then** 系统返回 "Content Not Found" 或类似状态。
2. **Given** 等待超时发生，**When** 系统处理超时，**Then** 记录原因并继续处理其他条目。

---

### Edge Cases

- 网络延迟导致加载缓慢：超时设置应足够宽容，避免误判。
- 页面部分加载：应等待关键内容元素而非整个页面。
- 多种错误同时出现：优先识别最明确的错误指示器。
- 推文内容为空（如纯图片推文）：应有备用检测策略。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 使用内容元素检测替代固定时间等待。
- **FR-002**: 系统 MUST 在检测到推文内容元素后立即提取，无额外等待。
- **FR-003**: 系统 MUST 支持最长 15 秒的内容等待超时。
- **FR-004**: 系统 MUST 在 2 秒内检测并报告登录墙。
- **FR-005**: 系统 MUST 快速检测并报告服务器错误页面。
- **FR-006**: 系统 MUST 在超时时返回明确的错误状态和原因。
- **FR-007**: 系统 MUST 移除现有的固定 sleep 等待逻辑。
- **FR-008**: 系统 SHOULD 支持并行检测多种错误指示器。

### Assumptions

- 推文内容元素在 React 渲染完成后可见。
- 登录墙和错误页面有可识别的特征元素。
- 15 秒超时足以覆盖大多数正常加载场景。
- 2 秒足够检测登录墙（通常立即显示）。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 正常推文的平均等待时间从 10 秒降至 < 5 秒。
- **SC-002**: 登录墙检测时间 ≤ 2 秒。
- **SC-003**: 服务器错误检测时间 ≤ 3 秒。
- **SC-004**: 超时场景有明确的错误消息和状态标记。
- **SC-005**: 移除所有固定 sleep 调用，无硬编码等待时间。
- **SC-006**: 错误检测准确率 ≥ 95%（无误报正常推文）。
