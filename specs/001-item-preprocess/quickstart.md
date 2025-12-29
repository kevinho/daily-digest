# Quickstart: Item Preprocessing (Name + URL/Content completeness)

## Prereqs

- Notion credentials set: `NOTION_TOKEN`, `NOTION_DATABASE_ID` (and optional `NOTION_DATA_SOURCE_ID`), status/select schema includes `Name`, `URL`, `Raw Content`, `Status`, `Reason`/`Notes`.
- Chrome with remote debugging: `CHROME_REMOTE_URL` (default `http://localhost:9222`) and running with user profile that can open target URLs.
- Python env (3.11) with `pip install -r requirements.txt`.
- Optional: `OPENAI_API_KEY` (not required for preprocessing but used by other flows).

## Env knobs (add to your `.env`)

- `PREPROCESS_AUTO=true|false` — run preprocessing automatically when `main.py` starts.
- `PREPROCESS_SCOPE=pending` — label for logs; scope uses existing `get_pending_tasks()` filter (To Read / pending / unprocessed / empty status).
- `LOG_LEVEL=INFO` — adjust verbosity.
- `TIMEZONE=Asia/Shanghai` — for digest timestamps (unchanged by preprocessing).

## Manual run

```bash
source .venv/bin/activate
python main.py --preprocess
```

Expected:
- Items with Name + URL/Content: skipped.
- Missing Name but URL/Content present: Name backfilled (URL title → first heading/line); Reason/Notes annotated.
- Name present but URL & Content missing: status → Error, Reason set.
- Counts logged: backfilled/error/skip.

## Auto run together with digest (optional)

```bash
export PREPROCESS_AUTO=true
python main.py --digest daily  # preprocess first, then digest as usual
```

## Troubleshooting

- If Name is not backfilled: check URL accessibility via the debug Chrome; ensure `Raw Content` is populated or attachments present.
- If Notion updates fail: verify `NOTION_TOKEN` scope and that Status column is `status` or `select`.
- If Reason/Notes not visible: ensure the database has a `Reason` (rich text) property or adjust env overrides (`NOTION_PROP_REASON` not needed unless renamed).
- CDP fetch errors: confirm Chrome remote debugging is running and accessible on `CHROME_REMOTE_URL`.

