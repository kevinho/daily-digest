# Feature Specification: Twitter 页面截图

**Feature Branch**: `006-twitter-screenshot`  
**Created**: 2025-12-29  
**Status**: Draft  
**Input**: User description: "当发现是 Twitter 页面，把页面的图片截取一下，放到 Files 这个字段"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 自动截取 Tweet 截图 (Priority: P1)

用户保存 Tweet 链接到 Notion，系统在处理时自动截取 Tweet 页面的截图，并保存到该条目的 Files 字段中。这样即使原推文被删除或账号被封禁，用户仍能看到原始内容的视觉记录。

**Why this priority**: 截图是内容保存的重要补充，可以作为原始内容的备份，特别是对于包含图片、视频缩略图或特殊排版的推文。

**Independent Test**: 处理一条 Tweet 后，检查 Notion 条目的 Files 字段是否包含该推文的截图文件。

**Acceptance Scenarios**:

1. **Given** 系统正在处理一条 Twitter URL，**When** 页面加载完成后，**Then** 系统截取页面截图并上传到 Notion 条目的 Files 字段。
2. **Given** Tweet 页面包含图片或视频，**When** 截图完成，**Then** 截图应包含完整的推文区域（包括媒体预览）。
3. **Given** 截图文件名，**When** 保存到 Notion，**Then** 文件名应包含推文 ID 以便识别（如 `tweet-123456789.png`）。

---

### User Story 2 - 截图失败不影响主流程 (Priority: P2)

即使截图失败（如页面加载超时、截图 API 错误），系统仍应继续处理其他内容（标题、正文提取），不应因截图失败而标记整个条目为 Error。

**Why this priority**: 截图是增强功能，不应影响核心的内容提取流程。

**Independent Test**: 模拟截图失败的场景，验证条目仍能正常处理并标记为 ready/pending。

**Acceptance Scenarios**:

1. **Given** 截图过程发生错误，**When** 系统捕获异常，**Then** 记录警告日志但继续处理，不标记为 Error。
2. **Given** 截图失败，**When** 条目处理完成，**Then** Reason 字段可注明"截图失败"但状态仍为 ready/pending。

---

### Edge Cases

- Tweet 页面需要滚动才能显示完整内容：截取可见区域即可，不要求全页面滚动截图。
- Tweet 已被删除或私密化：截图可能显示错误页面，此时截图仍保存（作为证据），但标题/正文提取应按原有逻辑标记 Error。
- 网络超时或 CDP 连接失败：截图跳过，记录日志，主流程继续。
- Files 字段不存在或类型错误：跳过截图上传，记录警告。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在处理 Twitter URL 时，于内容提取完成后截取页面截图。
- **FR-002**: 截图 MUST 保存为 PNG 格式，文件名格式为 `tweet-{tweet_id}.png`。
- **FR-003**: 系统 MUST 将截图上传到 Notion 条目的 Files 字段。
- **FR-004**: 截图失败时，系统 MUST 记录警告日志但不影响主流程。
- **FR-005**: 系统 SHOULD 仅截取主要推文区域（使用 `article[data-testid="tweet"]` 选择器），而非整个页面。
- **FR-006**: 截图功能 SHOULD 可通过配置开关控制（默认开启）。

### Key Entities

- **Screenshot**: 代表一次截图操作，包含文件路径、Tweet ID、截图状态（成功/失败）。
- **Files 字段**: Notion 条目中用于存储附件的字段，支持多个文件。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 对已登录状态下的 Tweet，截图成功率 ≥ 85%。
- **SC-002**: 截图失败不影响条目处理成功率（主流程成功率保持不变）。
- **SC-003**: 截图文件大小合理（单张 ≤ 2MB）。
- **SC-004**: 截图操作额外耗时 ≤ 3 秒。
