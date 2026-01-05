# Daily Digest

> 个人内容收集、分类、摘要系统 —— 从 Notion 数据库自动抓取网页内容，AI 生成摘要，输出递归汇总报告。

## ✨ 功能特性

- **内容收集**: 通过 Notion 数据库收集待处理的 URL 和笔记
- **自动分类**: 基于规则和 AI 进行内容分类和标签标注
- **AI 摘要**: 使用 OpenAI GPT 模型生成 TLDR 和要点提炼
- **递归汇总**: 支持日报→周报→月报的层级汇总系统
- **Twitter 支持**: 特殊处理 Twitter/X 链接，绕过反爬机制
- **去重机制**: 基于规范化 URL 自动检测和标记重复内容

---

## 📸 功能演示

### Inbox 数据库 - 内容收集

<!-- TODO: 添加 Inbox 数据库截图 -->
![Inbox Database](docs/images/inbox-placeholder.png)

### AI 摘要生成

<!-- TODO: 添加 AI 摘要效果截图 -->
![AI Summary](docs/images/summary-placeholder.png)

### 日报生成

<!-- TODO: 添加日报截图 -->
![Daily Report](docs/images/daily-report-placeholder.png)

### 周报/月报汇总

<!-- TODO: 添加周报/月报截图 -->
![Weekly Report](docs/images/weekly-report-placeholder.png)

### 演示视频

<!-- TODO: 添加演示视频链接 -->
> 🎬 [观看完整演示视频](https://your-video-link.com)

---

## 🚀 快速开始

详细安装步骤请参考 **[安装指南](docs/installation.md)**

```bash
# 1. 克隆 & 安装
git clone https://github.com/kevinho/daily-digest.git
cd daily-digest
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 Notion Token、数据库 ID、OpenAI Key

# 3. 启动 Chrome 远程调试
./start_chrome.sh

# 4. 运行
python -m venv .venv && source .venv/bin/activate
python main.py process       # 处理新内容
python main.py report --type daily   # 生成日报
```

---

## 📖 使用方式

### 处理新 Items

```bash
python main.py process
```

处理 Inbox 数据库中新收集的条目：预处理 → 内容抓取 → AI 摘要

### 生成报告

```bash
# 日报（汇总当天 ready 的 items）
python main.py report --type daily

# 周报（汇总本周的日报）
python main.py report --type weekly

# 月报（汇总本月的周报）
python main.py report --type monthly

# 指定日期 / 强制重新生成
python main.py report --type daily --date 2025-01-15
python main.py report --type daily --force
```

### 递归汇总架构

```
Level 4: Monthly ───┐
   ↑                │ 汇总 Weekly
Level 3: Weekly ────┤
   ↑                │ 汇总 Daily
Level 2: Daily ─────┤
   ↑                │ 汇总 Items
Level 1: Items ─────┘ (Inbox DB → status=ready)
```

---

## ⚙️ Notion 配置

系统需要 **2 个 Notion 数据库**：

| 数据库 | 用途 | 环境变量 |
|--------|------|----------|
| **Inbox DB** | 收集原始内容（URL、笔记） | `NOTION_ITEM_DB_ID`、`NOTION_ITEM_DS_ID` |
| **Report DB** | 存储生成的报告（日报/周报/月报） | `NOTION_REPORTING_DB_ID`、`NOTION_REPORTING_DS_ID` |

> 💡 `*_DS_ID` 用于同步数据库场景，如果使用普通数据库可留空。

### Inbox 数据库字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 条目标题 |
| URL | URL | 网页链接 |
| Status | Status | 处理状态（To Read → ready） |
| Tags | Multi-select | 分类标签 |
| Summary | Text | AI 摘要 |
| ContentType | Select | 内容类型（html/pdf/image...） |
| CreatedTime | Created time | 创建时间（用于日报筛选） |

### Report 数据库字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 报告标题 |
| Type | Select | Daily / Weekly / Monthly |
| Date | Date | 报告日期 |
| Summary | Text | AI 概述 |
| Source Items | Relation | 关联的 Inbox 条目 |
| Source Reports | Relation | 关联的子报告 |

---

## 📚 文档

- **[安装指南](docs/installation.md)** - 环境配置、依赖安装、Notion 设置
- **[架构说明](docs/architecture.md)** - 项目结构、工作流程、模块说明

---

## ❓ FAQ

<details>
<summary>没有 OpenAI API Key 可以用吗？</summary>

可以。系统会自动降级为简单截断模式，摘要质量会降低但功能正常。
</details>

<details>
<summary>Chrome 需要保持打开吗？</summary>

是的。`start_chrome.sh` 启动的 Chrome 实例需要保持运行，用于抓取需要登录态的页面（如 Twitter）。
</details>

<details>
<summary>支持哪些内容格式？</summary>

- ✅ 网页 URL（HTML）
- ✅ 纯文本笔记
- ⚠️ PDF/图片：仅存储为附件，暂不支持 OCR
</details>

<details>
<summary>process 和 report 有什么区别？</summary>

- `process`: 处理 Inbox 中新收集的内容（抓取+摘要），输出到 Inbox DB
- `report`: 生成汇总报告（日报/周报/月报），输出到 Report DB
</details>

---

## 📄 License

MIT License
