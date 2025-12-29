# Implementation Plan: Twitter 抓取与预处理优化

**Branch**: `004-twitter-opt` | **Date**: 2025-12-29 | **Spec**: specs/004-twitter-opt/spec.md  
**Input**: Feature specification from `/specs/004-twitter-opt/spec.md`

## Summary

预处理为必跑阶段，校验/回填必填字段并自动对 tweet 链接调用抓取；抓取运行在已登录、合法 CDP 浏览器中，支持插件来源，写入 Reason/Source/Canonical/Raw Content，阻断不中断流程，幂等去重，可重试。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Playwright (CDP/反爬配置), notion-client, httpx/requests；预处理与抓取同流程。  
**Storage**: Notion Data Source DB（字段含 Reason、Source、Canonical、Raw Content）。  
**Testing**: pytest（单测/集成）。  
**Target Platform**: macOS 桌面，已登录的调试 Chrome（remote debugging）或 Playwright 启动浏览器。  
**Project Type**: 单仓库 Python CLI/批处理。  
**Performance Goals**: 单条抓取 p95 ≤5s、可访问时成功率≥90%；批量几十条 ≤1min。  
**Constraints**: 仅用合法浏览器会话；私有/不可访问标 Error；阻断不写错误正文；幂等去重；反爬参数可配置（env）。  
**Scale/Scope**: 个人/小规模（几十到上百条）。  

## Constitution Check

- 可信/合规：仅在合法登录浏览器中抓取，私有/不可访问标 Error。  
- 结构化捕获：写入 Name/URL/Raw Content/Status/Reason/Source/Canonical/Tags。  
- 隐私/安全：不越权、不外传，仅存 Notion。  
- 质量与可追溯：阻断→Error+Reason；成功→ready/pending；幂等去重。  
Gate: 通过。

## Project Structure

### Documentation (this feature)

```text
specs/004-twitter-opt/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── browser.py        # CDP fetch/anti-bot configurable
├── notion.py         # Notion manager (Reason+Source)
├── utils.py          # env/logging
├── preprocess.py     # required-field preprocessing
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

**Structure Decision**: 沿用单项目 Python，预处理/抓取集成在 main.py + helpers。

## Complexity Tracking

无违宪复杂度需豁免。
