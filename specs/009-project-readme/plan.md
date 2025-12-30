# Implementation Plan: Project README

**Branch**: `009-project-readme` | **Date**: 2025-12-30 | **Spec**: specs/009-project-readme/spec.md  
**Input**: Feature specification from `/specs/009-project-readme/spec.md`

## Summary

创建项目 README.md 文件，包含项目简介、功能特性、安装步骤、环境配置、使用方式和项目结构说明。

## Technical Context

**Language/Version**: Markdown  
**Primary Dependencies**: 无（纯文档）  
**Storage**: 项目根目录 `README.md`  
**Testing**: 人工验证  
**Target Platform**: GitHub / 本地仓库  
**Project Type**: 文档  
**Performance Goals**: N/A  
**Constraints**: 无  
**Scale/Scope**: 个人项目

## Constitution Check

| 原则 | 合规情况 |
|------|----------|
| I. 可信/合规 | ✅ 不涉及数据处理 |
| II. 结构化捕获 | ✅ 不涉及 |
| III. 隐私/安全 | ✅ 不包含敏感信息 |
| IV. 质量与可追溯 | ✅ 文档包含版本信息 |
| V. 反馈与安全自动化 | ✅ 不涉及 |

**Gate**: 通过。

## README Structure

```markdown
# Daily Digest

> 一句话简介

## ✨ 功能特性
- 内容收集
- 自动分类
- AI 摘要
- Digest 生成

## 📋 环境要求
- Python 3.11+
- Chrome (远程调试)
- Notion API Token
- OpenAI API Key (可选)

## 🚀 快速开始
### 1. 克隆项目
### 2. 安装依赖
### 3. 配置环境变量
### 4. 启动 Chrome
### 5. 运行

## ⚙️ 环境变量
完整 .env 模板

## 📖 使用方式
### 预处理
### 生成 Digest
### 完整流程

## 🏗️ 项目结构
目录树 + 模块说明

## 🔄 工作流程
数据流图

## ❓ FAQ
常见问题解答

## 📄 License
```

## Key Implementation Points

### 1. 项目简介 (FR-001, FR-002)

- 项目名称: Daily Digest
- 一句话简介: 个人内容收集、分类、摘要系统
- 核心功能列表

### 2. 环境配置 (FR-003, FR-004, FR-005)

完整的 `.env` 模板:

```bash
# Notion Configuration - Inbox DB
NOTION_TOKEN=secret_xxx
NOTION_ITEM_DB_ID=xxx
NOTION_ITEM_DS_ID=xxx            # 可选

# Notion Configuration - Report DB
NOTION_REPORTING_DB_ID=xxx
NOTION_REPORTING_DS_ID=xxx       # 可选

# Chrome Remote Debug
CHROME_REMOTE_URL=http://localhost:9222

# OpenAI (可选)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# Other
TZ=Asia/Shanghai
CONFIDENCE_THRESHOLD=0.5
TWITTER_SCREENSHOT_ENABLE=false
```

### 3. 使用说明 (FR-006)

主要命令:

```bash
# 启动 Chrome 远程调试
./start_chrome.sh

# 运行预处理
python main.py --preprocess

# 生成 Digest
python main.py --digest daily

# 完整流程
python main.py --digest daily
```

### 4. 项目结构 (FR-007)

```
daily-digest/
├── main.py              # 主入口
├── start_chrome.sh      # Chrome 启动脚本
├── requirements.txt     # 依赖
├── src/
│   ├── browser.py       # 网页内容抓取
│   ├── notion.py        # Notion API 交互
│   ├── llm.py           # AI 摘要/分类
│   ├── digest.py        # Digest 构建
│   ├── preprocess.py    # 预处理逻辑
│   ├── routing.py       # 条目路由
│   ├── dedupe.py        # 去重逻辑
│   └── utils.py         # 工具函数
├── scripts/             # 辅助脚本
├── tests/               # 测试
└── specs/               # 功能规格
```

### 5. 工作流程 (FR-008)

```
Notion 数据库 (待处理条目)
        ↓
    预处理 (preprocess)
    - 校验字段
    - 补齐标题
    - 分类路由
        ↓
    内容抓取 (browser)
    - Chrome CDP
    - 页面内容提取
        ↓
    AI 处理 (llm)
    - 分类
    - 摘要生成
        ↓
    Digest 构建 (digest)
    - 综合概述
    - 按类型分组
        ↓
Notion 输出 (Digest 页面)
```

## Complexity Tracking

无违宪复杂度需豁免。纯文档任务。

