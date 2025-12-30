# 架构说明

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
│   ├── notion.py        # Notion API 交互（Inbox DB）
│   ├── llm.py           # AI 摘要/分类（OpenAI）
│   ├── content_type.py  # 内容类型检测
│   ├── preprocess.py    # 预处理（字段校验、标题补齐）
│   ├── routing.py       # 条目类型路由
│   ├── dedupe.py        # URL 去重逻辑
│   ├── digest.py        # Digest 构建逻辑
│   ├── utils.py         # 工具函数
│   │
│   ├── handlers/        # 内容处理器
│   │   ├── base.py      # 基类
│   │   ├── registry.py  # 处理器注册表
│   │   ├── twitter.py   # Twitter/X 专用处理
│   │   ├── generic.py   # 通用 HTML 处理
│   │   ├── pdf.py       # PDF 处理
│   │   └── fallback.py  # 兜底处理
│   │
│   └── reporting/       # 递归汇总报告模块
│       ├── models.py           # 数据模型（ReportType, ReportPeriod）
│       ├── date_utils.py       # 日期范围计算
│       ├── builder.py          # 报告构建器（Daily/Weekly/Monthly）
│       ├── service.py          # 报告生成服务
│       └── notion_reporting.py # Notion API 交互（Report DB）
│
├── docs/                # 文档
├── scripts/             # 辅助脚本
├── tests/               # 测试
└── specs/               # 功能规格文档
```

---

## 🔄 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        系统架构                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │  python main.py  │      │  python main.py  │                 │
│  │     process      │      │     report       │                 │
│  │  (处理新 items)   │      │  (生成报告)       │                 │
│  └────────┬─────────┘      └────────┬─────────┘                 │
│           │                         │                            │
│           ▼                         ▼                            │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │    Inbox DB      │──────▶│   Report DB      │                 │
│  │   (原始条目)      │      │ (Daily/Weekly/   │                 │
│  │                  │      │  Monthly 报告)    │                 │
│  └──────────────────┘      └──────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 数据流

### Process 流程（处理新 Items）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Inbox DB   │────▶│   预处理     │────▶│  内容抓取    │────▶│  AI 摘要    │
│ (To Read)   │     │ (分类/补齐)  │     │ (Playwright) │     │ (OpenAI)   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
                                                                    ▼
                                                           ┌─────────────┐
                                                           │  Inbox DB   │
                                                           │  (ready)    │
                                                           └─────────────┘
```

### Report 流程（递归汇总）

```
┌─────────────┐
│  Inbox DB   │
│  (ready)    │
└──────┬──────┘
       │ 汇总当天 items
       ▼
┌─────────────┐
│ Daily Report│
└──────┬──────┘
       │ 汇总本周 daily
       ▼
┌─────────────┐
│Weekly Report│
└──────┬──────┘
       │ 汇总本月 weekly
       ▼
┌──────────────┐
│Monthly Report│
└──────────────┘
```

---

## 🧩 核心模块说明

| 模块 | 职责 |
|------|------|
| `browser.py` | 通过 Chrome CDP 抓取网页内容，支持反爬绕过 |
| `notion.py` | Notion API 封装（Inbox DB），查询、更新、创建页面 |
| `llm.py` | OpenAI 调用，生成摘要、概述、分类 |
| `content_type.py` | 检测 URL 内容类型（HTML/PDF/Image/Video...） |
| `preprocess.py` | 预处理流程，校验字段、补齐标题、路由分类 |
| `routing.py` | 条目类型判断（URL_RESOURCE / NOTE_CONTENT / EMPTY_INVALID） |

### Handlers 模块

| Handler | 匹配规则 | 处理方式 |
|---------|----------|----------|
| `TwitterHandler` | `x.com`, `twitter.com` | 截图 + 文本提取 |
| `GenericHandler` | HTML 类型 | trafilatura 提取 |
| `PDFHandler` | PDF 类型 | 文件名作为标题 |
| `FallbackHandler` | 其他类型 | 标记为 ready |

### Reporting 模块

| 组件 | 职责 |
|------|------|
| `models.py` | 定义 ReportType、ReportPeriod、ReportData |
| `date_utils.py` | 计算日/周/月的日期范围 |
| `builder.py` | 构建报告内容（DailyBuilder、WeeklyBuilder、MonthlyBuilder） |
| `service.py` | 报告生成服务，协调各组件 |
| `notion_reporting.py` | Report DB 的 Notion API 交互 |

---

## 🔧 ContentType 检测流程

```
URL
 │
 ├─▶ 检查扩展名 (.pdf, .jpg, .mp4...)
 │    │
 │    └─▶ 匹配 → 返回对应类型
 │
 ├─▶ HTTP HEAD 请求
 │    │
 │    └─▶ 解析 Content-Type header
 │
 └─▶ 域名推断
      │
      └─▶ 已知 HTML 域名 (weixin.qq.com...) → HTML
```

---

## 🏷️ 两级分类系统

Daily Report 使用 AI 进行两级分类：

```
主类别（Level 1）
├── 子类别 A
│   ├── Item 1
│   └── Item 2
├── 子类别 B
│   └── Item 3
...

示例：
技术
├── AI工具 (3条)
│   ├── 📌 斯坦福大学将其AI学位课程免费公开...
│   └── 📌 Chatterbox开源语音模型...
├── 开源项目 (2条)
│   └── 📌 本周热门的公共代理技能库...
投资
├── 交易策略 (2条)
│   └── 📌 交易员分享四重背离策略...
```

