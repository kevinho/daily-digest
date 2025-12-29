# Feature Specification: Project README

**Feature Branch**: `009-project-readme`  
**Created**: 2025-12-30  
**Status**: Draft  
**Input**: 为这个项目增加readme，介绍使用方式

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 快速了解项目 (Priority: P1)

新用户访问项目仓库，需要在 1 分钟内了解这个项目是做什么的、有什么价值。

**Why this priority**: 项目介绍是用户接触项目的第一入口，决定用户是否继续深入了解。

**Independent Test**: 访问项目根目录，验证 README.md 存在且包含项目简介、核心功能描述。

**Acceptance Scenarios**:

1. **Given** 用户首次访问项目，**When** 打开 README，**Then** 能在 1 分钟内理解项目用途和核心功能。
2. **Given** README 已存在，**When** 用户阅读项目简介，**Then** 清楚了解这是一个个人内容收集、分类、摘要系统。

---

### User Story 2 - 快速启动项目 (Priority: P1)

开发者希望在本地运行这个项目，需要清晰的环境准备和启动步骤。

**Why this priority**: 能否快速运行是开发者评估项目可用性的关键。

**Independent Test**: 按照 README 步骤，验证新环境能成功运行项目。

**Acceptance Scenarios**:

1. **Given** 用户有 Python 3.11 环境，**When** 按照 README 步骤操作，**Then** 能在 5 分钟内完成环境配置。
2. **Given** 环境已配置，**When** 执行主命令，**Then** 项目能正常运行。
3. **Given** README 包含环境变量说明，**When** 用户查阅，**Then** 清楚需要配置哪些 API 密钥和服务。

---

### User Story 3 - 了解使用方式 (Priority: P1)

用户希望了解项目的主要使用场景和命令参数。

**Why this priority**: 使用说明决定用户能否正确使用项目功能。

**Independent Test**: 验证 README 包含所有主要命令的使用示例。

**Acceptance Scenarios**:

1. **Given** 用户想运行预处理，**When** 查看 README，**Then** 找到 `--preprocess` 参数说明和示例。
2. **Given** 用户想生成摘要，**When** 查看 README，**Then** 找到 `--digest` 参数说明和示例。
3. **Given** 用户需要启动 Chrome 调试，**When** 查看 README，**Then** 找到 `start_chrome.sh` 脚本说明。

---

### User Story 4 - 了解项目架构 (Priority: P2)

开发者想了解项目的模块结构和各模块职责。

**Why this priority**: 架构说明帮助开发者快速定位代码，但不影响基本使用。

**Independent Test**: 验证 README 包含项目结构图和模块职责说明。

**Acceptance Scenarios**:

1. **Given** 用户查看项目结构，**When** 阅读 README，**Then** 了解 `src/` 下各模块（browser、notion、llm、digest）的职责。
2. **Given** 用户想了解数据流，**When** 阅读 README，**Then** 理解 Notion → 预处理 → 内容抓取 → AI 摘要 → Digest 的流程。

---

### Edge Cases

- 用户无 Notion 账号：说明需要先创建 Notion 数据库并获取 API Token。
- 用户无 OpenAI API Key：说明降级方案（简单截断替代 AI 摘要）。
- Chrome 未安装：说明需要安装 Chrome 并配置路径。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: README MUST 包含项目名称和一句话简介。
- **FR-002**: README MUST 包含功能特性列表（内容收集、分类、摘要、Digest 生成）。
- **FR-003**: README MUST 包含环境要求（Python 版本、依赖库）。
- **FR-004**: README MUST 包含安装步骤（克隆、安装依赖、配置环境变量）。
- **FR-005**: README MUST 包含环境变量配置说明（完整的 `.env` 模板）。
- **FR-006**: README MUST 包含使用方式（命令行参数、示例）。
- **FR-007**: README MUST 包含项目结构说明（主要目录和模块）。
- **FR-008**: README SHOULD 包含工作流程图或说明。
- **FR-009**: README SHOULD 包含常见问题（FAQ）或故障排除。

### Key Entities

- **README.md**: 项目根目录的说明文档，使用 Markdown 格式。
- **Environment Variables**: 配置项集合，包括 API 密钥、数据库 ID 等。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新用户能在 1 分钟内通过 README 理解项目用途。
- **SC-002**: 开发者能在 5 分钟内按照 README 完成环境配置。
- **SC-003**: README 覆盖所有主要命令（`main.py`、`start_chrome.sh`）的使用说明。
- **SC-004**: README 包含完整的环境变量模板，用户复制后只需填入实际值即可使用。
- **SC-005**: 项目结构说明覆盖所有 `src/` 下的核心模块。
