# Research: Twitter 内容读取

## Decisions
- 使用已登录的合法 Chrome/CDP 会话，避免越权。Playwright 启动时默认带反爬参数（关闭 AutomationControlled、覆盖 UA/viewport、注入 init_script 抹 webdriver/伪插件）。阻断时返回错误，不写正文。
- URL 必须是 tweet 链接，短链需先解析；无效或被登录墙/JS 阻断时标记 Error+Reason。
- save to notion 插件产生的条目复用同一抓取逻辑，仅补充来源标记。

## Rationale
- 登录态+真实浏览器最可靠地通过登录墙与 JS 检测；通用反爬参数可降低被识别概率。
- 明确 URL 校验与阻断处理可避免污染数据。

## Alternatives Considered
- 纯 HTTP 抓取：受登录/JS/反爬限制大，放弃。
- 专用 API/抓包：涉及合规和凭证风险，放弃。***

