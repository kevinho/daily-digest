# Implementation Plan: Twitter 页面截图

**Branch**: `006-twitter-screenshot` | **Date**: 2025-12-29 | **Spec**: specs/006-twitter-screenshot/spec.md  
**Input**: Feature specification from `/specs/006-twitter-screenshot/spec.md`

## Summary

在处理 Twitter 页面时，自动截取推文区域的截图并上传到 Notion 条目的 Files 字段，作为原始内容的视觉备份。截图失败不影响主内容提取流程。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Playwright (已有，用于截图)、notion-client (已有，用于上传)  
**Storage**: Notion Files 字段；临时文件存储截图后上传  
**Testing**: pytest  
**Target Platform**: macOS，已登录调试 Chrome  
**Project Type**: 单仓库 Python CLI  
**Performance Goals**: 截图额外耗时 ≤ 3s，单张 ≤ 2MB  
**Constraints**: 截图失败不阻断主流程；可配置开关  
**Scale/Scope**: 个人使用

## Constitution Check

| 原则 | 合规情况 |
|------|----------|
| I. 可信/合规 | ✅ 截图来自合法登录浏览器，保存到用户自己的 Notion |
| II. 结构化捕获 | ✅ 截图作为附件存储在 Files 字段，与条目关联 |
| III. 隐私/安全 | ✅ 截图仅保存到用户 Notion，不外传 |
| IV. 质量与可追溯 | ✅ 截图文件名包含 Tweet ID，可追溯 |
| V. 反馈与安全自动化 | ✅ 截图失败记录日志，不影响主流程 |

**Gate**: 通过。

## Project Structure

### Documentation (this feature)

```text
specs/006-twitter-screenshot/
├── plan.md              # 本文件
├── quickstart.md        # 快速入门
├── checklists/
│   └── requirements.md  # 规格检查清单
└── tasks.md             # 任务清单
```

### Source Code (repository root)

```text
src/
├── browser.py           # 核心：添加 capture_tweet_screenshot() 函数
├── notion.py            # 添加 upload_file_to_item() 方法
├── utils.py             # 添加 TWITTER_SCREENSHOT_ENABLE 配置
└── ...

tests/
├── test_browser.py      # 添加截图相关测试
└── ...

tmp/                     # 临时目录（存放截图文件，上传后删除）
```

**Structure Decision**: 继续单项目 Python 布局，核心改动集中在 `src/browser.py`（截图）和 `src/notion.py`（上传）。

## Key Implementation Points

### 1. 截图函数 (`src/browser.py`)

```python
async def capture_tweet_screenshot(
    page,
    tweet_id: str,
    output_dir: str = "tmp"
) -> Optional[str]:
    """
    截取推文区域截图。
    
    Returns: 截图文件路径，失败返回 None
    """
    try:
        # 尝试定位推文元素
        tweet_el = page.locator('article[data-testid="tweet"]').first
        if await tweet_el.count() == 0:
            # 回退到全页面截图
            path = f"{output_dir}/tweet-{tweet_id}.png"
            await page.screenshot(path=path, full_page=False)
            return path
        
        # 截取推文元素
        path = f"{output_dir}/tweet-{tweet_id}.png"
        await tweet_el.screenshot(path=path)
        return path
    except Exception as e:
        logger.warning(f"Screenshot failed for {tweet_id}: {e}")
        return None
```

### 2. Notion 文件上传 (`src/notion.py`)

```python
def upload_file_to_item(self, page_id: str, file_path: str, field_name: str = "Files"):
    """
    上传文件到 Notion 条目的 Files 字段。
    
    Note: Notion API 不直接支持文件上传，需要使用外部 URL。
    方案：将截图上传到临时存储（如 Notion 自带的 S3），然后关联到条目。
    """
    # Notion API 限制：Files 字段只能引用外部 URL
    # 方案 A: 使用 Notion 的内部文件上传（需要先 POST 到 /v1/files）
    # 方案 B: 上传到其他存储（S3/Cloudflare R2），然后引用 URL
    # 简化方案: 将截图 base64 存入 Rich Text 字段（不推荐，太大）
    pass
```

### 3. 配置开关 (`src/utils.py`)

```python
TWITTER_SCREENSHOT_ENABLE = _parse_bool(os.getenv("TWITTER_SCREENSHOT_ENABLE"), True)
```

### 4. 集成到主流程 (`main.py`)

在 `process_item` 中，Twitter 内容提取成功后：

```python
if is_twitter and TWITTER_SCREENSHOT_ENABLE:
    screenshot_path = await capture_tweet_screenshot(page, tweet_id)
    if screenshot_path:
        notion.upload_file_to_item(page_id, screenshot_path)
        os.remove(screenshot_path)  # 清理临时文件
```

## Research Notes

### Notion Files 字段上传方案

**问题**: Notion API 的 Files 字段只能引用外部 URL，不能直接上传二进制文件。

**可选方案**:

| 方案 | 优点 | 缺点 |
|------|------|------|
| A. Notion 内部上传 API | 原生支持 | API 较新，文档不完善 |
| B. 外部存储 (S3/R2) | 稳定可靠 | 需要额外配置和成本 |
| C. GitHub Gist/Release | 免费 | 不适合图片存储 |
| D. 本地文件路径 | 最简单 | 只能本地访问 |

**推荐**: 方案 A - 使用 Notion 的 `/v1/files` 端点上传，然后关联到 Files 字段。如果 API 不可用，回退到方案 D（本地路径记录到 Reason 字段）。

## Complexity Tracking

无违宪复杂度需豁免。
