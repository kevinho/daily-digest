# Tasks: Smart Waiters for Twitter Content

**Branch**: `010-smart-waiters` | **Date**: 2025-12-30  
**Spec**: specs/010-smart-waiters/spec.md | **Plan**: specs/010-smart-waiters/plan.md

## US1 - 快速获取有效推文内容 (P1)

**Goal**: 检测到推文内容后立即提取，平均等待 < 5 秒。

### Tasks

- [ ] **T001**: 定义 `TwitterWaitResult` 枚举（SUCCESS, LOGIN_WALL, SERVER_ERROR, TIMEOUT）
- [ ] **T002**: 实现 `_twitter_smart_wait()` 函数，使用 `wait_for_selector` 检测内容元素
- [ ] **T003**: 修改 `fetch_page_content()` 对 Twitter 使用 smart wait

**Independent Test**: 正常推文链接在内容可见后立即提取。

---

## US2 - 快速识别登录墙 (P1)

**Goal**: 2 秒内检测登录墙并报告错误。

### Tasks

- [ ] **T004**: 定义 `TwitterLoginWallError` 异常类
- [ ] **T005**: 在 `_twitter_smart_wait()` 中添加登录墙检测（`[data-testid="login"]`, 2s timeout）

**Independent Test**: 登录墙场景在 2 秒内检测到。

---

## US3 - 快速识别服务器错误 (P1)

**Goal**: 快速检测服务器错误并报告。

### Tasks

- [ ] **T006**: 定义 `TwitterServerError` 异常类
- [ ] **T007**: 在 `_twitter_smart_wait()` 中添加错误检测（`span:has-text("Something went wrong")`, 3s timeout）

**Independent Test**: 服务器错误页面快速检测。

---

## US4 - 优雅处理超时 (P2)

**Goal**: 超时返回明确状态，降级到 meta 提取。

### Tasks

- [ ] **T008**: 实现超时后的降级逻辑（继续 meta 提取）
- [ ] **T009**: 确保超时有明确的错误消息

**Independent Test**: 已删除推文在超时后返回明确状态。

---

## 清理工作

### Tasks

- [ ] **T010**: 修改 `_wait_delay_ms()` 对 Twitter 返回 0
- [ ] **T011**: 标记 `_get_twitter_wait_ms()` 为 deprecated 或移除

---

## MVP / Incremental Strategy

| 阶段 | 任务 | 可验证结果 |
|------|------|------------|
| Phase 1 | T001-T003 | Smart wait 基础功能 |
| Phase 2 | T004-T005 | 登录墙快速检测 |
| Phase 3 | T006-T007 | 服务器错误检测 |
| Phase 4 | T008-T009 | 超时降级处理 |
| Phase 5 | T010-T011 | 清理旧代码 |

---

## Progress Tracking

| Task | Status | Notes |
|------|--------|-------|
| T001 | ✅ | TwitterWaitResult enum |
| T002 | ✅ | _twitter_smart_wait() |
| T003 | ✅ | fetch_page_content() updated |
| T004 | ✅ | TwitterLoginWallError |
| T005 | ✅ | Login selector in smart wait |
| T006 | ✅ | TwitterServerError |
| T007 | ✅ | Error selector in smart wait |
| T008 | ✅ | Timeout fallback to meta |
| T009 | ✅ | Clear timeout messages |
| T010 | ✅ | _wait_delay_ms() returns 0 |
| T011 | ✅ | _get_twitter_wait_ms() deprecated |

