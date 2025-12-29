# Tasks: Twitter 抓取与预处理优化 (004-twitter-opt)

**Input**: spec/plan for `004-twitter-opt`  
**Prerequisites**: Notion 字段齐备（Reason/Source/Canonical/Raw Content），已登录的调试 Chrome/CDP 可用。

格式：`- [ ] T001 [P] [US1] description with file path`

## Phase 1: Setup

- [ ] T001 [P] 校验 Notion schema（Reason/Source/Canonical/Raw Content）：`python scripts/check_schema.py`
- [ ] T002 [P] 更新 env 文档/示例（`.env.example` 或 quickstart）：补充 `CHROME_REMOTE_URL` 与 `ANTI_BOT_*` 示例。

---

## Phase 2: Foundational (Blocking)

- [ ] T010 确认 `main.py` 启动必跑 `run_preprocess`，阻断/异常不崩溃，写 Reason；scope 可配置。
- [ ] T011 确认 `src/browser.py` 复用已登录 CDP context（无则创建），阻断检测返回可用错误信息。
- [ ] T012 在 `main.py` 保持统计日志（success/error/duplicate/unprocessed）并不中断。

**Checkpoint**: 预处理必跑、阻断可追溯、流程不中断。

---

## Phase 3: User Story 1 - 预处理必跑 + Twitter 抓取内置 🎯

- [ ] T020 [US1] 预处理调用 Twitter 规范化+抓取：`main.py` 使用 `normalize_tweet_url` 后调用 fetch，写 Raw Content/Canonical/Source/Reason/Status。
- [ ] T021 [US1] 阻断/无效 tweet：Error+Reason，不写正文；流程继续。
- [ ] T022 [P] [US1] 测试：混合条目（普通+tweet）；阻断/无效 URL；统计计数不中断：`tests/test_twitter_ingest.py`。

---

## Phase 4: User Story 2 - 条目清晰度提升 🎯

- [ ] T030 [US2] 写入/读取 Source、Reason、Raw Content、Canonical；已 ready/pending 的 Canonical 跳过或关联 Duplicate：`src/notion.py` `main.py`。
- [ ] T031 [P] [US2] 标题清洗：Name 为空/默认/域名时，抓取 title 失败则用 “Bookmark:{domain}” 或内容前 20 字/“Image Clip”：`main.py`/`preprocess.py`（如需）。
- [ ] T032 [P] [US2] 测试：插件来源写 Source=plugin；重复 ready/pending 不重复写入；标题清洗用例：`tests/test_twitter_ingest.py`。

---

## Phase 5: User Story 3 - 稳定性与可恢复 (P2)

- [ ] T040 [US3] 重试/恢复：阻断后重跑可成功；抓取异常不崩溃，计数/Reason 正确：`main.py`。
- [ ] T041 [P] [US3] 配置化反爬验证：env 覆盖 UA/viewport/init_script/args，重跑可成功或返回明确错误：`src/browser.py` 测试/文档。
- [ ] T042 [P] [US3] Quickstart 故障排查补充：登录过期、CDP 端口、反爬参数切换：`specs/004-twitter-opt/quickstart.md`。

---

## Phase 6: Polish & Cross-Cutting

- [ ] T050 [P] 端到端自测并记录示例日志（计数输出 + 示例 Reason），附在 quickstart/README。
- [ ] T051 [P] 如需，新增监控/简单 metrics 钩子（抓取结果计数）或补充日志级别说明。

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1(P1) → US2(P1) → US3(P2) → Polish。  
- 测试标记 [P] 可并行，建议先写测试再实现。  
- 预处理必跑；阻断/异常需不中断批处理；标题清洗/合法性校验对所有条目生效。  

