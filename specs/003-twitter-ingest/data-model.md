# Data Model: Twitter 内容读取

## Entities

- **Tweet Item**
  - Fields: Name (title), URL, Raw Content (rich text), Summary/备注, Status (status/select), Reason (rich text), Canonical URL, Tags, Duplicate Of, Rule Version, Prompt Version, Source (手动/插件)。
  - Notes: Reason 必填；Status ready/pending/error/unprocessed；Canonical 用于去重。

- **Capture Job** (逻辑实体，用于日志/计数)
  - Fields: Item ID, Source (手动/插件), Result (success/error), Reason, Duration, Timestamp。

## Relationships
- Tweet Item may link to Duplicate Of (relation) for去重。

## Validation
- URL 必须为 tweet 链接；无效/阻断 → Status=Error, Reason 记录。***

