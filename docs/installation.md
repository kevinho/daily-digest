# 安装指南

## 📋 环境要求

- **Python**: 3.11+
- **Chrome**: 需安装 Google Chrome（用于远程调试抓取页面）
- **Notion**: 需要 Notion Integration Token 和 2 个数据库
- **OpenAI**: API Key（可选，无则使用简单截断替代）

---

## 🚀 安装步骤

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
```

编辑 `.env` 文件：

```bash
# ===================
# Notion 配置 - Inbox 数据库
# ===================
NOTION_TOKEN=secret_xxx                 # Notion Integration Token
NOTION_ITEM_DB_ID=xxx                   # Inbox 数据库 ID
NOTION_ITEM_DS_ID=xxx                   # Inbox Data Source ID（同步数据库用，可选）

# ===================
# Notion 配置 - Report 数据库
# ===================
NOTION_REPORTING_DB_ID=xxx              # Report 数据库 ID
NOTION_REPORTING_DS_ID=xxx              # Report Data Source ID（同步数据库用，可选）

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
```

### 4. 启动 Chrome 远程调试

```bash
./start_chrome.sh
```

这会启动一个带远程调试端口的 Chrome 实例，用于抓取需要登录的页面内容。

环境变量：
- `CHROME_BIN`: Chrome 可执行文件路径（默认 macOS 路径）
- `DEBUG_PORT`: 调试端口（默认 9222）

### 5. 验证安装

```bash
# 测试 Notion 连接
python -c "from src.notion import NotionManager; print('Notion OK')"

# 测试 Chrome CDP
curl http://localhost:9222/json/version
```

---

## 🔧 Notion 配置

### 创建 Integration

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 点击「New integration」
3. 填写名称，选择关联的 Workspace
4. 复制 `Internal Integration Token`（即 `NOTION_TOKEN`）

### 创建数据库

系统需要 **2 个数据库**：

#### Inbox 数据库（收集原始内容）

创建数据库并添加以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 条目标题 |
| URL | URL | 网页链接 |
| Status | Status | 处理状态 |
| Tags | Multi-select | 分类标签 |
| Summary | Text | AI 摘要 |
| ContentType | Select | 内容类型 |
| ItemType | Select | 条目类型 |
| Files | Files | 附件/截图 |
| CreatedDate | Created time | 创建时间（用于日报筛选） |

Status 字段建议配置：
- `To Read` - 待处理
- `ready` - 已处理完成
- `Error` - 处理出错

#### Report 数据库（存储报告）

创建数据库并添加以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Name | Title | 报告标题 |
| Type | Select | Daily / Weekly / Monthly |
| Date | Date | 报告开始日期 |
| Period End | Date | 报告结束日期 |
| Summary | Text | AI 概述 |
| Highlights | Text | 要点提炼 |
| Source Items | Relation | 关联 Inbox 条目 |
| Source Reports | Relation | 关联子报告（自关联） |
| Status | Status | 报告状态 |

### 连接 Integration

对于每个数据库：

1. 打开数据库页面
2. 点击右上角「...」→「Connections」
3. 添加你创建的 Integration

### 获取数据库 ID

数据库 URL 格式：
```
https://www.notion.so/workspace/DATABASE_ID?v=...
```

复制 32 位的 `DATABASE_ID` 到对应环境变量。

### 获取 Data Source ID（同步数据库）

如果你使用的是 **同步数据库**（Synced Database），需要额外获取 Data Source ID：

1. 打开数据库页面，点击右上角「...」
2. 选择「Copy link to view」
3. URL 格式如下：
   ```
   https://www.notion.so/workspace/DATABASE_ID?v=VIEW_ID&pvs=4
   ```
4. 使用 Notion API 查询数据库信息：
   ```bash
   curl -X GET "https://api.notion.com/v1/databases/DATABASE_ID" \
     -H "Authorization: Bearer YOUR_NOTION_TOKEN" \
     -H "Notion-Version: 2022-06-28" | jq '.id, .parent'
   ```
5. 对于同步数据库，响应中会包含 `parent.type: "block_id"` 或相关信息
6. 或者直接在浏览器开发者工具的 Network 面板中，查看 Notion 请求，找到 `spaceId` 或 `data_source_id`

> 💡 **提示**：普通数据库不需要 Data Source ID，留空即可。只有从外部同步的数据库（如 Google Calendar、GitHub 等）才需要配置。

**简便方法**：运行以下脚本自动获取：
```bash
python scripts/get_datasource_id.py --database-id YOUR_DATABASE_ID
```

---

## 🐛 常见问题

### Playwright 未安装

```
RuntimeError: playwright is required to fetch page content
```

解决：
```bash
pip install playwright
playwright install chromium
```

### Chrome CDP 连接失败

```
Error: connect ECONNREFUSED 127.0.0.1:9222
```

解决：
1. 确保已运行 `./start_chrome.sh`
2. 检查端口是否被占用：`lsof -i :9222`
3. 验证 CDP 可用：`curl http://localhost:9222/json/version`

### Notion API 错误

```
notion_client.errors.APIResponseError: Could not find database
```

解决：
1. 检查 `NOTION_ITEM_DB_ID` 是否正确
2. 确保 Integration 已添加到数据库 Connections
3. 确保 Integration 有足够权限（Read & Update）

