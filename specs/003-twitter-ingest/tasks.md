# Tasks: Twitter 内容读取

**Input**: spec/plan for `003-twitter-ingest`  
**Prerequisites**: `Reason` 等 Notion 字段已存在；可用的登录 Chrome/CDP。

格式：`- [ ] T001 [P] [US1] description with file path`

## Phase 1: Setup

- [ ] T001 [P] 运行并验证 Notion 字段（含 Reason）齐全：`python scripts/check_schema.py`

---

## Phase 2: Foundational (Blocking)

- [ ] T010 在 `src/browser.py` 增加反爬配置入口（AutomationControlled/UA/viewport/init_script 可配置），默认启用。
- [ ] T011 在 `src/utils.py` 添加 tweet URL 校验/规范化工具，返回错误时供管线直接标记 Error。
- [ ] T012 在 `src/browser.py` 增加阻断检测（登录墙/JS 提示），返回明确错误消息（供 Reason 使用），不返回错误正文。

**Checkpoint**: 反爬配置 & 阻断检测可复用，URL 校验可用。

---

## Phase 3: User Story 1 - 基础抓取（CDP 合法浏览器） 🎯

- [ ] T020 [US1] 在 `src/browser.py` 实现 Twitter/X 抓取函数，使用反爬配置，返回正文/错误原因。
- [ ] T021 [US1] 在 `main.py` 集成 Twitter 抓取路径：检测 tweet URL，调用抓取，写入 Raw Content/Reason/Status。
- [ ] T022 [P] [US1] 在 `tests/test_twitter_ingest.py` 编写用例：成功抓取、阻断返回 Error、无效 URL 返回 Error。

---

## Phase 4: User Story 2 - 插件深度抓取（save to notion） 🎯

- [ ] T030 [US2] 支持插件保存的 Twitter 条目：在 `main.py`/Notion 更新时标记来源（插件/手动），复用 Twitter 抓取逻辑并写必需字段。
- [ ] T031 [P] [US2] 在 `tests/test_twitter_ingest.py` 添加用例：插件来源成功抓取；插件 URL 无效/阻断 → Error+Reason。

---

## Phase 5: User Story 3 - 幂等与重复防护 (Priority: P2)

- [ ] T040 [US3] 在 `main.py` 增加 tweet Canonical URL 去重/幂等策略：已 ready/pending 的条目跳过，不重复写入。
- [ ] T041 [P] [US3] 在 `tests/test_twitter_ingest.py` 添加用例：重复运行不重复写入；先失败后解封再成功。

---

## Phase 6: Polish & Cross-Cutting

- [ ] T050 [P] 更新 `specs/003-twitter-ingest/quickstart.md`：登录步骤、反爬参数示例、运行命令与预期。
- [ ] T051 [P] 在 `main.py` 增加抓取结果日志/计数（success/error/blocked）便于排查。
- [ ] T052 [P] 在 `.env.example` 增补反爬相关配置示例（UA、init_script 开关、CHROME_REMOTE_URL），并说明默认值。

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1(P1) → US2(P1) → US3(P2) → Polish。  
- 测试与实现可在同一阶段标记 [P] 并行，但先写测试再实现为佳。  
- 反爬配置/阻断检测完成后，US1/US2/US3 可并行开发各自逻辑。

