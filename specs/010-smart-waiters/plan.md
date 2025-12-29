# Implementation Plan: Smart Waiters for Twitter Content

**Branch**: `010-smart-waiters` | **Date**: 2025-12-30 | **Spec**: specs/010-smart-waiters/spec.md  
**Input**: Feature specification from `/specs/010-smart-waiters/spec.md`

## Summary

替换 `_wait_delay_ms()` 固定等待为智能等待策略，使用 Playwright 的 `wait_for_selector` 实现内容检测和错误快速识别。

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: playwright (已有)  
**Storage**: 无  
**Testing**: pytest + mock  
**Target Platform**: macOS CLI  
**Project Type**: 单仓库 Python CLI  
**Performance Goals**: 正常推文等待 < 5s，登录墙检测 ≤ 2s  
**Constraints**: 保持向后兼容  
**Scale/Scope**: 个人使用

## Constitution Check

| 原则 | 合规情况 |
|------|----------|
| I. 可信/合规 | ✅ 不涉及数据收集变更 |
| II. 结构化捕获 | ✅ 不涉及 |
| III. 隐私/安全 | ✅ 不涉及 |
| IV. 质量与可追溯 | ✅ 错误原因明确记录 |
| V. 反馈与安全自动化 | ✅ 提供明确错误状态 |

**Gate**: 通过。

## Project Structure

### Source Code Changes

```text
src/
└── browser.py    # 主要修改：替换 _wait_delay_ms + 新增 smart waiter 函数
```

### Key Selectors (Twitter)

```python
# 内容元素
TWEET_TEXT_SELECTOR = 'div[data-testid="tweetText"]'
TWEET_ARTICLE_SELECTOR = 'article[data-testid="tweet"]'

# 错误指示器
LOGIN_WALL_SELECTOR = '[data-testid="login"]'
ERROR_TEXT_SELECTOR = 'span:has-text("Something went wrong")'
```

## Key Implementation Points

### 1. Smart Waiter 函数

```python
class TwitterWaitResult:
    """Result of smart wait operation."""
    SUCCESS = "success"
    LOGIN_WALL = "login_wall"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"

async def _twitter_smart_wait(page, timeout_ms: int = 15000) -> tuple[str, str]:
    """
    Smart wait for Twitter content with fast failure detection.
    
    Returns:
        (result_type, message)
    """
    # Race conditions: content vs error indicators
    try:
        # Start all waiters
        content_task = asyncio.create_task(
            page.wait_for_selector(
                'div[data-testid="tweetText"], article[data-testid="tweet"]',
                timeout=timeout_ms
            )
        )
        login_task = asyncio.create_task(
            page.wait_for_selector('[data-testid="login"]', timeout=2000)
        )
        error_task = asyncio.create_task(
            page.wait_for_selector('span:has-text("Something went wrong")', timeout=3000)
        )
        
        # Wait for first to complete
        done, pending = await asyncio.wait(
            [content_task, login_task, error_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
        
        # Determine result
        completed = done.pop()
        if completed == content_task:
            return (TwitterWaitResult.SUCCESS, "Content loaded")
        elif completed == login_task:
            return (TwitterWaitResult.LOGIN_WALL, "Login Wall Detected")
        elif completed == error_task:
            return (TwitterWaitResult.SERVER_ERROR, "Twitter Server Error")
            
    except asyncio.TimeoutError:
        return (TwitterWaitResult.TIMEOUT, "Content Not Found (timeout)")
    except Exception as e:
        return (TwitterWaitResult.TIMEOUT, f"Wait failed: {e}")
```

### 2. 集成到 fetch_page_content

```python
async def fetch_page_content(...):
    # ... existing code ...
    
    await page.goto(url, wait_until="load", timeout=timeout_ms)
    
    # Smart wait for Twitter
    if is_twitter:
        result, message = await _twitter_smart_wait(page, timeout_ms=15000)
        if result == TwitterWaitResult.LOGIN_WALL:
            raise TwitterLoginWallError(message)
        elif result == TwitterWaitResult.SERVER_ERROR:
            raise TwitterServerError(message)
        elif result == TwitterWaitResult.TIMEOUT:
            # Continue with meta extraction as fallback
            pass
    else:
        # Non-Twitter: keep simple delay
        await page.wait_for_timeout(1500)
    
    # Continue with content extraction...
```

### 3. 自定义异常类

```python
class TwitterFetchError(Exception):
    """Base error for Twitter fetching."""
    pass

class TwitterLoginWallError(TwitterFetchError):
    """Twitter login wall detected."""
    pass

class TwitterServerError(TwitterFetchError):
    """Twitter server error."""
    pass
```

### 4. 移除固定等待

- 移除对 `TWITTER_WAIT_MS` 环境变量的依赖
- 移除 `_get_twitter_wait_ms()` 函数（或标记为 deprecated）
- 修改 `_wait_delay_ms()` 对 Twitter 返回 0（由 smart waiter 处理）

## Error Handling

| 场景 | 检测方式 | 响应 |
|------|----------|------|
| 正常内容 | `tweetText` 元素可见 | 返回内容 |
| 登录墙 | `login` 元素出现 | 抛出 TwitterLoginWallError |
| 服务器错误 | "Something went wrong" | 抛出 TwitterServerError |
| 超时 | 15s 无内容 | 尝试 meta 提取降级 |

## Complexity Tracking

无违宪复杂度需豁免。

