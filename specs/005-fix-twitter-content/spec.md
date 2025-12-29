# Feature Specification: 修复 Twitter 内容获取

**Feature Branch**: `005-fix-twitter-content`  
**Created**: 2025-12-29  
**Status**: Draft  
**Input**: 解决 Twitter 内容获取问题，使用 Hybrid 策略提取

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 可靠获取 Tweet 正文 (Priority: P1)

用户保存 Tweet 链接到 Notion，系统能可靠抓取 Tweet 文字内容。

**Extraction Strategy (Hybrid)**:
- **Priority 1 (Meta Tags)**: 从 `<link type="application/json+oembed">` 或 `<meta property="og:title">` 即时获取内容
- **Priority 2 (DOM)**: 如 Meta 不足，等待 `div[data-testid="tweetText"]` 加载

**Acceptance Scenarios**:

1. **Given** 已登录 Twitter 的调试 Chrome，**When** 处理普通文本 Tweet，**Then** 能从 oembed/og:title 或 DOM 提取完整文字。
2. **Given** 页面需要加载时间，**When** Meta Tags 不含完整内容，**Then** 等待 DOM 加载后提取。
3. **Given** 检测到登录墙/阻断，**When** 提取失败，**Then** 标记 Error 并写入 Reason。

---

### User Story 2 - 正确获取 Tweet 标题 (Priority: P1)

系统从 Tweet 页面获取有意义的标题（"Author on X: content..."）。

**Acceptance Scenarios**:

1. **Given** Tweet 页面加载完成，**When** 提取标题，**Then** 返回 og:title 或 oembed title。
2. **Given** 标题为空或错误提示，**When** 检测到，**Then** 从正文首行生成标题。

---

### User Story 3 - 减少页面打开次数 (Priority: P2)

同一 URL 在处理中只打开一次，使用缓存。

**Acceptance Scenarios**:

1. **Given** 需要同时获取标题和正文，**When** 处理 Tweet，**Then** 只导航一次，缓存结果。
2. **Given** 重试次数默认 1，**When** 首次成功，**Then** 不触发额外重试。

---

### Edge Cases

- Tweet 已删除/私密：标记 Error
- 纯媒体 Tweet：标记 "Media-only tweet"
- 长 Tweet：完整提取
- 网络超时：友好报错
- CDP 未启动：明确提示

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MUST 优先从 `<link type="application/json+oembed">` 的 title 属性提取 Tweet 内容
- **FR-002**: MUST 从 `<meta property="og:title">` 提取标题
- **FR-003**: SHOULD 仅当 Meta 不足时，等待 `div[data-testid="tweetText"]` DOM 元素
- **FR-004**: MUST 缓存已抓取结果，同一 URL 只打开一次
- **FR-005**: MUST 支持 `TWITTER_WAIT_MS`、`PAGE_FETCH_RETRIES` 配置
- **FR-006**: MUST 检测登录墙/阻断，标记 Error + Reason
- **FR-007**: MUST 对非 Twitter 保持 trafilatura 提取逻辑

### Key Entities

- **PageCache**: 按 URL 存储标题和正文
- **HostExtractor**: 按域名分发提取策略

## Success Criteria *(mandatory)*

- **SC-001**: Tweet 正文提取成功率 ≥ 90%
- **SC-002**: 单条处理只打开 1 次页面
- **SC-003**: 阻断 100% 有 Reason
- **SC-004**: 标题提取成功率 ≥ 95%

