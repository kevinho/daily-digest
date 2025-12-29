# Implementation Plan: Twitter 抓取与预处理优化

**Branch**: `004-twitter-opt` | **Date**: 2025-12-29 | **Spec**: specs/004-twitter-opt/spec.md  
**Input**: Feature specification from `/specs/004-twitter-opt/spec.md`

## Summary

预处理为必跑阶段：校验/回填必填字段并自动对 tweet 链接调用抓取；抓取在已登录、合法 CDP 浏览器中执行，阻断/无效写 Reason 不中断；记录 Source/Reason/Canonical/Raw Content，重复去重，支持插件来源，重试可恢复。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Playwright (CDP、反爬配置), notion-client, httpx/requests；预处理与抓取同流程。  
**Storage**: Notion Data Source DB（字段含 Reason、Source、Canonical、Raw Content）。  
**Testing**: pytest（单测/集成）。  
**Target Platform**: macOS 桌面，已登录的调试 Chrome（remote debugging）或 Playwright 启动浏览器。  
**Project Type**: 单仓库 Python CLI/批处理。  
**Performance Goals**: 单条抓取 p95 ≤5s、可访问时成功率 ≥90%；小批量（几十条）≤1min。  
**Constraints**: 仅用合法浏览器会话；私有/不可访问标 Error；阻断不写错误正文；幂等去重；反爬参数 env 可配；预处理必跑。  
**Scale/Scope**: 个人/小规模（几十到上百条）。

## Constitution Check

- 可信/合规：仅在合法登录浏览器中抓取，私有/不可访问标 Error。  
- 结构化捕获：写入 Name/URL/Raw Content/Status/Reason/Source/Canonical/Tags。  
- 隐私/安全：不越权、不外传，仅存 Notion。  
- 质量与可追溯：阻断→Error+Reason；成功→ready/pending；幂等去重。  
**Gate**: 通过。

## Project Structure

### Documentation (this feature)

```text
specs/004-twitter-opt/
├── plan.md
├── research.md          # Phase 0（若需补充决策）
├── data-model.md        # Phase 1（若需补充实体）
├── quickstart.md        # Phase 1（运行/排查示例）
├── contracts/           # Phase 1（如需对外接口）
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── browser.py        # CDP fetch/anti-bot configurable
├── preprocess.py     # 必跑预处理
├── notion.py         # Reason+Source+Canonical
├── utils.py          # env/anti-bot settings
├── dedupe.py
├── digest.py
└── llm.py

scripts/
├── check_schema.py
└── start_chrome.sh

tests/
├── test_twitter_ingest.py
└── test_preprocess.py
```

**Structure Decision**: 单项目 Python，预处理与抓取在 main 流程中一体化，复用反爬/去重/日志统计。

## Complexity Tracking

无违宪复杂度需豁免。

