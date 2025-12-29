# Quickstart: 智能条目路由 (007-smart-item-routing)

## 功能概述

自动识别条目类型并执行相应处理：

| 类型 | 判断条件 | 处理方式 |
|------|----------|----------|
| URL_RESOURCE | URL 字段有值 | 抓取 → 分类 → 摘要 |
| NOTE_CONTENT | 无 URL，有内容块 | 命名 NOTE-日期-序号 → ready |
| EMPTY_INVALID | 无 URL，无内容 | 标记 Error |

## 运行

```bash
source .venv/bin/activate
python main.py --digest daily
```

## 分类流程

```
classify_item(item_data, notion)
  │
  ├─ URL 字段有值?
  │   └─ Yes → URL_RESOURCE
  │
  ├─ No → 调用 blocks.children.list(page_size=1)
  │   ├─ 有内容块? → NOTE_CONTENT
  │   └─ 无内容 → EMPTY_INVALID
```

## 预期行为

| 场景 | 预期结果 |
|------|----------|
| 保存带 URL 的书签 | 识别为 URL_RESOURCE，执行抓取 |
| 保存纯文本笔记 | 识别为 NOTE_CONTENT，直接 ready |
| 保存图片剪辑 | 识别为 NOTE_CONTENT，直接 ready |
| 创建空条目 | 识别为 EMPTY_INVALID，标记 Error |

## NOTE 命名规则

格式: `NOTE-YYYYMMDD-N`

示例:
- NOTE-20251229-1
- NOTE-20251229-2
- NOTE-20251230-1

## API 调用优化

- URL 字段检查：纯本地操作，无 API 调用
- 内容块检测：`page_size=1` 最小化响应数据
- 每个无 URL 条目最多 1 次 blocks API 调用

## 排查

- **NOTE_CONTENT 未识别**: 检查内容块是否为空段落
- **序号重复**: 检查同一天已有多少 NOTE 条目
- **API 调用过多**: 确认 page_size=1 参数正确传递

