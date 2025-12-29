# Daily Digest

> 个人内容收集、分类、摘要系统 —— 从 Notion 数据库自动抓取网页内容，AI 生成摘要，输出结构化 Digest。

## ✨ 功能特性

- **内容收集**: 通过 Notion 数据库收集待处理的 URL 和笔记
- **自动分类**: 基于规则和 AI 进行内容分类和标签标注
- **AI 摘要**: 使用 OpenAI GPT 模型生成 TLDR 和要点提炼
- **Digest 生成**: 自动生成结构化摘要页面，包含综合概述和分类条目
- **Twitter 支持**: 特殊处理 Twitter/X 链接，支持截图保存
- **去重机制**: 基于规范化 URL 自动检测和标记重复内容

## 📋 环境要求

- **Python**: 3.11+
- **Chrome**: 需安装 Google Chrome（用于远程调试抓取页面）
- **Notion**: 需要 Notion Integration Token 和数据库
- **OpenAI**: API Key（可选，无则使用简单截断替代）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/kevinho/daily-digest.git
cd daily-digest
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板并填入实际值：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥和配置
```

### 4. 启动 Chrome 远程调试

```bash
./start_chrome.sh
```

这会启动一个带远程调试端口的 Chrome 实例，用于抓取需要登录的页面内容。

### 5. 运行

```bash
# 运行完整流程（预处理 + 内容抓取 + 生成 Digest）
python main.py --digest daily
```

## ⚙️ 环境变量

在项目根目录创建 `.env` 文件：

```bash
# ===================
# Notion 配置
# ===================
NOTION_TOKEN=secret_xxx                 # Notion Integration Token
NOTION_DATABASE_ID=xxx                  # 收集数据库 ID
NOTION_DATA_SOURCE_ID=xxx               # 可选，Data Source ID（同步数据库）
NOTION_DIGEST_PARENT_ID=xxx             # Digest 输出的父页面 ID

# ===================
# Chrome 远程调试
# ===================
CHROME_REMOTE_URL=http://localhost:9222 # Chrome DevTools Protocol 地址

# ===================
# OpenAI 配置（可选）
# ===================
OPENAI_API_KEY=sk-xxx                   # OpenAI API Key
OPENAI_MODEL=gpt-4o-mini                # 使用的模型

# ===================
# 其他配置
# ===================
TZ=Asia/Shanghai                        # 时区
CONFIDENCE_THRESHOLD=0.5                # 分类置信度阈值
TWITTER_SCREENSHOT_ENABLE=false         # 是否启用 Twitter 截图
PREPROCESS_SCOPE=pending                # 预处理范围
```

### 获取 Notion 配置

1. 创建 [Notion Integration](https://www.notion.so/my-integrations)，获取 `NOTION_TOKEN`
2. 创建收集用数据库，获取 `NOTION_DATABASE_ID`（URL 中的 32 位 ID）
3. 将 Integration 添加到数据库的 Connections 中
4. 创建一个空白页面用于存放 Digest，获取 `NOTION_DIGEST_PARENT_ID`

### Notion 数据库字段

数据库需要包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 条目标题 |
| URL | URL | 网页链接 |
| Status | Status/Select | 处理状态 |
| Tags | Multi-select | 分类标签 |
| Summary | Text | AI 摘要 |
| Files | Files | 附件/截图 |

## 📖 使用方式

### 仅运行预处理

校验字段、补齐标题、分类路由：

```bash
python main.py --preprocess
```

### 生成 Digest

处理待处理条目并生成 Digest 页面：

```bash
# 日报
python main.py --digest daily

# 周报
python main.py --digest weekly

# 自定义标签
python main.py --digest custom
```

### 完整流程

预处理 + 内容抓取 + AI 摘要 + Digest 生成：

```bash
python main.py --digest daily
```

### Chrome 远程调试

启动带调试端口的 Chrome（用于抓取需要登录的页面）：

```bash
./start_chrome.sh
```

环境变量：
- `CHROME_BIN`: Chrome 可执行文件路径（默认 macOS 路径）
- `DEBUG_PORT`: 调试端口（默认 9222）

## 🏗️ 项目结构

```
daily-digest/
├── main.py              # 主入口，CLI 命令处理
├── start_chrome.sh      # Chrome 远程调试启动脚本
├── requirements.txt     # Python 依赖
├── .env                 # 环境变量配置（需自行创建）
│
├── src/                 # 核心模块
│   ├── browser.py       # 网页内容抓取（Playwright + CDP）
│   ├── notion.py        # Notion API 交互
│   ├── llm.py           # AI 摘要/分类（OpenAI）
│   ├── digest.py        # Digest 构建逻辑
│   ├── preprocess.py    # 预处理（字段校验、标题补齐）
│   ├── routing.py       # 条目类型路由
│   ├── dedupe.py        # URL 去重逻辑
│   └── utils.py         # 工具函数
│
├── scripts/             # 辅助脚本
│   ├── notion_align_schema.py  # 数据库 Schema 对齐
│   └── db_crud_demo.py         # Notion CRUD 示例
│
├── tests/               # 测试
└── specs/               # 功能规格文档
```

### 核心模块说明

| 模块 | 职责 |
|------|------|
| `browser.py` | 通过 Chrome CDP 抓取网页内容，支持 Twitter 特殊处理 |
| `notion.py` | Notion API 封装，包括查询、更新、创建页面 |
| `llm.py` | OpenAI 调用，生成摘要、概述、分类 |
| `digest.py` | 构建 Digest 数据结构，按 ItemType 分组 |
| `preprocess.py` | 预处理流程，校验字段、补齐标题、路由分类 |
| `routing.py` | 条目类型判断（URL_RESOURCE / NOTE_CONTENT / EMPTY_INVALID） |
| `dedupe.py` | URL 规范化和重复检测 |
| `utils.py` | 日志配置、环境变量读取、时区处理 |

## 🔄 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     Notion 数据库                                │
│                   (待处理条目: To Read)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      预处理 (preprocess)                         │
│  • 校验必填字段 (Name, URL/Content)                              │
│  • 补齐缺失标题                                                  │
│  • 路由分类 (URL_RESOURCE / NOTE_CONTENT / EMPTY_INVALID)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     内容抓取 (browser)                           │
│  • 连接 Chrome CDP                                               │
│  • 抓取页面 HTML                                                 │
│  • 提取正文内容 (trafilatura)                                    │
│  • Twitter 特殊处理 + 截图                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI 处理 (llm)                               │
│  • 内容分类 + 标签                                               │
│  • 生成 TLDR 摘要                                                │
│  • 提取要点 (Highlights)                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Digest 构建 (digest)                          │
│  • 生成综合概述 (100-150字)                                      │
│  • 按 ItemType 分组                                              │
│  • 构建结构化输出                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Notion 输出                                  │
│                   (Digest 页面)                                  │
│  📋 综合概述                                                     │
│  🔗 网页内容 (标题 + 要点 + 链接)                                 │
│  📝 笔记内容 (标题 + 链接)                                        │
└─────────────────────────────────────────────────────────────────┘
```

## ❓ FAQ

### Q: 没有 OpenAI API Key 可以用吗？

可以。系统会自动降级为简单截断模式，摘要质量会降低但功能正常。

### Q: Chrome 需要保持打开吗？

是的。`start_chrome.sh` 启动的 Chrome 实例需要保持运行，用于抓取需要登录态的页面（如 Twitter）。

### Q: 如何处理 Twitter/X 链接？

系统会自动识别 Twitter 链接并进行特殊处理：
- 规范化 URL 格式
- 使用 CDP 绕过反爬
- 可选启用截图保存（`TWITTER_SCREENSHOT_ENABLE=true`）

### Q: 支持哪些内容格式？

- ✅ 网页 URL（HTML）
- ✅ 纯文本笔记
- ⚠️ PDF/图片：仅存储为附件，暂不支持 OCR

### Q: 如何添加新的待处理内容？

1. 直接在 Notion 数据库中添加新行
2. 填写 URL 或内容
3. Status 设为 "To Read" 或留空
4. 运行 `python main.py --digest daily`

### Q: Digest 输出在哪里？

Digest 会创建为 `NOTION_DIGEST_PARENT_ID` 指定页面的子页面，标题格式为 `Digest (daily) 2025-01-01 12:00`。

## 📄 License

MIT License

