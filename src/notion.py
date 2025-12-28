from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from notion_client import Client

from src.utils import get_env


@dataclass(frozen=True)
class StatusNames:
    pending: str = "pending"
    ready: str = "ready"
    excluded: str = "excluded"
    error: str = "Error"
    unprocessed: str = "unprocessed"
    to_read: str = "To Read"


@dataclass(frozen=True)
class PropertyNames:
    status: str = "Status"
    url: str = "URL"
    summary: str = "Summary"
    confidence: str = "Confidence"
    sensitivity: str = "Sensitivity"
    files: str = "Files"
    canonical_url: str = "Canonical URL"
    duplicate_of: str = "Duplicate Of"
    tags: str = "Tags"
    rule_version: str = "Rule Version"
    prompt_version: str = "Prompt Version"


class NotionManager:
    def __init__(self) -> None:
        token = get_env("NOTION_TOKEN", required=True)
        self.database_id = get_env("NOTION_DATABASE_ID", required=True)
        self.client = Client(auth=token)

        self.status = StatusNames(
            pending=get_env("NOTION_STATUS_PENDING", StatusNames.pending),
            ready=get_env("NOTION_STATUS_READY", StatusNames.ready),
            excluded=get_env("NOTION_STATUS_EXCLUDED", StatusNames.excluded),
            error=get_env("NOTION_STATUS_ERROR", StatusNames.error),
            unprocessed=get_env("NOTION_STATUS_UNPROCESSED", StatusNames.unprocessed),
            to_read=get_env("NOTION_STATUS_TO_READ", StatusNames.to_read),
        )

        self.prop = PropertyNames(
            status=get_env("NOTION_PROP_STATUS", PropertyNames.status),
            url=get_env("NOTION_PROP_URL", PropertyNames.url),
            summary=get_env("NOTION_PROP_SUMMARY", PropertyNames.summary),
            confidence=get_env("NOTION_PROP_CONFIDENCE", PropertyNames.confidence),
            sensitivity=get_env("NOTION_PROP_SENSITIVITY", PropertyNames.sensitivity),
            files=get_env("NOTION_PROP_FILES", PropertyNames.files),
            canonical_url=get_env("NOTION_PROP_CANONICAL_URL", PropertyNames.canonical_url),
            duplicate_of=get_env("NOTION_PROP_DUPLICATE_OF", PropertyNames.duplicate_of),
            tags=get_env("NOTION_PROP_TAGS", PropertyNames.tags),
            rule_version=get_env("NOTION_PROP_RULE_VERSION", PropertyNames.rule_version),
            prompt_version=get_env("NOTION_PROP_PROMPT_VERSION", PropertyNames.prompt_version),
        )

    def _simplify_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        url = props.get(self.prop.url, {}).get("url")
        files_prop = props.get(self.prop.files, {})
        attachments: List[str] = []
        if isinstance(files_prop, dict) and "files" in files_prop:
            for f in files_prop.get("files", []):
                ftype = f.get("type")
                if ftype and isinstance(f.get(ftype), dict):
                    link = f[ftype].get("url")
                    if link:
                        attachments.append(link)
        status_prop = props.get(self.prop.status, {})
        status_name = None
        if "status" in status_prop and isinstance(status_prop["status"], dict):
            status_name = status_prop["status"].get("name")
        return {
            "id": page.get("id"),
            "url": url,
            "attachments": attachments,
            "status": status_name,
            "raw": page,
        }

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Fetch pages whose status is To Read/pending/unprocessed."""
        resp = self.client.databases.query(
            **{
                "database_id": self.database_id,
                "filter": {
                    "or": [
                        {"property": self.prop.status, "status": {"equals": self.status.to_read}},
                        {"property": self.prop.status, "status": {"equals": self.status.pending}},
                        {"property": self.prop.status, "status": {"equals": self.status.unprocessed}},
                    ]
                },
            }
        )
        return [self._simplify_page(p) for p in resp.get("results", [])]

    def find_by_canonical(self, canonical_url: str) -> Optional[Dict[str, Any]]:
        resp = self.client.databases.query(
            **{
                "database_id": self.database_id,
                "filter": {
                    "property": self.prop.canonical_url,
                    "url": {"equals": canonical_url},
                },
            }
        )
        results = resp.get("results", [])
        if not results:
            return None
        return self._simplify_page(results[0])

    def _update_status(self, page_id: str, status: str, extra_props: Optional[Dict[str, Any]] = None) -> None:
        props: Dict[str, Any] = {self.prop.status: {"status": {"name": status}}}
        if extra_props:
            props.update(extra_props)
        self.client.pages.update(page_id=page_id, properties=props)

    def mark_as_done(self, page_id: str, summary: str, status: Optional[str] = None) -> None:
        props = {
            self.prop.summary: {"rich_text": [{"text": {"content": summary[:1900]}}]},
        }
        target_status = status or self.status.ready
        self._update_status(page_id, target_status, props)

    def mark_as_error(self, page_id: str, error: str) -> None:
        props = {
            self.prop.summary: {"rich_text": [{"text": {"content": f"Error: {error}"[:1900]}}]},
        }
        self._update_status(page_id, self.status.error, props)

    def mark_unprocessed(self, page_id: str, note: str) -> None:
        props = {
            self.prop.summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
        }
        self._update_status(page_id, self.status.unprocessed, props)

    def mark_excluded(self, page_id: str, note: str) -> None:
        props = {
            self.prop.summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
        }
        self._update_status(page_id, self.status.excluded, props)

    def fetch_ready_for_digest(self, since: Optional[str], until: Optional[str]) -> List[Dict[str, Any]]:
        filters: List[Dict[str, Any]] = [
            {"property": self.prop.status, "status": {"equals": self.status.ready}},
        ]
        if since or until:
            # Assume Created time for now; adjust to a date property if schema differs
            date_filter: Dict[str, Any] = {"timestamp": "created_time", "created_time": {}}
            if since:
                date_filter["created_time"]["on_or_after"] = since
            if until:
                date_filter["created_time"]["on_or_before"] = until
            filters.append(date_filter)
        resp = self.client.databases.query(
            **{
                "database_id": self.database_id,
                "filter": {"and": filters},
            }
        )
        return [self._simplify_page(p) for p in resp.get("results", [])]

    def set_duplicate_of(self, page_id: str, canonical_id: str, note: str) -> None:
        props = {
            self.prop.duplicate_of: {"relation": [{"id": canonical_id}]},
            self.prop.summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
        }
        self._update_status(page_id, self.status.excluded, props)

    def set_classification(
        self,
        page_id: str,
        tags: List[str],
        sensitivity: str,
        confidence: float,
        rule_version: str,
        prompt_version: str,
    ) -> None:
        props: Dict[str, Any] = {
            self.prop.tags: {"multi_select": [{"name": t} for t in tags]},
            self.prop.sensitivity: {"select": {"name": sensitivity}},
            self.prop.confidence: {"number": confidence},
            self.prop.rule_version: {"rich_text": [{"text": {"content": rule_version}}]},
            self.prop.prompt_version: {"rich_text": [{"text": {"content": prompt_version}}]},
        }
        self.client.pages.update(page_id=page_id, properties=props)
