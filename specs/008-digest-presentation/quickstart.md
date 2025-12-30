# Quickstart: Digest 内容呈现优化 (008-digest-presentation)

## 功能概述

优化 Digest 输出结构：

| 部分 | 内容 | 长度 |
|------|------|------|
| 综合概述 | 批次整体主题和要点 | 100-150 字（~30s 阅读） |
| 分条目摘要 | 标题 + Highlights + URL | 每条 3-5 个 highlights |
| 标签分组 | 按 Tags 分组显示 | - |

## 运行

```bash
source .venv/bin/activate
python main.py --digest daily
```

## 输出结构

```
📋 Daily Digest - 2025-12-30

📊 统计: 8条 | AI: 3条 | 产品: 2条 | 行业: 3条

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 综合概述

本批次共收集 8 条内容，涵盖 AI 技术（3条）、产品设计（2条）、
行业动态（3条）。核心关注：语音克隆技术突破...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【AI 技术】

📌 Chatterbox Turbo 语音克隆
  • 首次响应时间小于 150ms
  • 仅需 5 秒音频实现克隆
  • MIT 开源许可
  🔗 https://x.com/...

📌 RAG 架构新进展
  • 支持多模态检索
  • 性能提升 40%
  🔗 https://...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【产品设计】

📌 ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

引用: page_id_1, page_id_2, ...
```

## 数据结构

```python
{
    "overview": "综合概述文本",
    "tag_groups": [
        {
            "tag": "AI",
            "items": [
                {
                    "title": "Chatterbox Turbo",
                    "highlights": ["要点1", "要点2"],
                    "url": "https://..."
                }
            ]
        }
    ],
    "citations": ["page_id_1", "page_id_2"]
}
```

## 降级方案

无 AI 时：
- 综合概述：`"本批次共 N 条内容，涵盖 X（n条）、Y（m条）..."`
- Highlights：从 summary 按句号切分前 3 句

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| OPENAI_API_KEY | OpenAI API Key | - |
| OPENAI_MODEL | 模型名称 | gpt-4o-mini |
| NOTION_REPORTING_DB_ID | Report 数据库 ID | - |

