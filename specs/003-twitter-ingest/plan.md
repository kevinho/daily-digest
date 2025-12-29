# Implementation Plan: Twitter 内容读取

**Branch**: `003-twitter-ingest` | **Date**: 2025-12-29 | **Spec**: specs/003-twitter-ingest/spec.md  
**Input**: Feature specification from `/specs/003-twitter-ingest/spec.md`

## Summary

启动时先跑预处理，校验/回填必填字段并对 tweet 链接自动调用抓取；抓取在已登录、合法 CDP 浏览器中规避反爬与登录墙；支持 save to notion 插件保存的条目，字段一致并标记来源；重复运行幂等，失败可重试。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Playwright (CDP/反爬规避)、notion-client、httpx/requests；预处理/抓取在同一流程中运行。可选 OpenAI/trafilatura 仅用于其他功能，非本抓取核心。  
**Storage**: Notion Data Source DB（字段含 Reason + Source + Canonical URL + Raw Content 等）。  
**Testing**: pytest（单测/集成）。  
**Target Platform**: macOS 桌面，已登录的调试 Chrome（remote debugging）或 Playwright 启动的合法浏览器。  
**Project Type**: 单仓库 Python CLI/批处理。  
**Performance Goals**: 单条抓取 p95 ≤5s，在登录可访问时成功率≥90%；批量（几十条）≤1min。  
**Constraints**: 必须使用合法浏览器会话；不抓取私有/不可访问内容；阻断时写 Reason，不写错误正文；保持幂等，避免重复写入；预处理是必跑阶段（开机先跑）。  
**Scale/Scope**: 个人/小规模（几十到上百条）。  

## Constitution Check

- 可信/合规：仅在用户已登录合法浏览器内抓取，尊重访问控制；私有/不可访问标记 Error，不越权。  
- 结构化捕获：写入 schema（Name/URL/Raw Content/Status/Reason/Canonical URL/Tags...），保留来源与状态。  
- 隐私/安全：不越权抓取，不外传数据；仅存 Notion。  
- 质量与可追溯：阻断→Error+Reason；成功→状态 ready/pending；重复运行幂等。  
Gate: 通过。

## Project Structure

### Documentation (this feature)

```text
specs/003-twitter-ingest/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md   # by /speckit.tasks
```

### Source Code (repository root)

```text
src/
├── browser.py        # CDP fetch; will add anti-bot args/init scripts when needed
├── notion.py         # Notion manager (Reason required)
├── utils.py          # env/logging
└── ...

scripts/
└── check_schema.py   # schema check (Reason required)

tests/
└── ... (add test_twitter_ingest.py)
```

**Structure Decision**: 继续单项目 Python；在 `src/browser.py` 增加反爬配置入口；在 orchestrator/handler 中增加 Twitter 路径处理。

## Complexity Tracking

无违宪复杂度需豁免。*** End Patch going to functions.apply_patch ***!
