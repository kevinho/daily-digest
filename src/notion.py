from typing import Any, Dict, List, Optional

from notion_client import Client

from src.utils import get_env


STATUS_PENDING = "pending"
STATUS_READY = "ready"
STATUS_EXCLUDED = "excluded"
STATUS_ERROR = "Error"
STATUS_UNPROCESSED = "unprocessed"


class NotionManager:
    def __init__(self) -> None:
        token = get_env("NOTION_TOKEN", required=True)
        self.database_id = get_env("NOTION_DATABASE_ID", required=True)
        self.client = Client(auth=token)
        # Property names (allow override via env if schema differs)
        self.prop_status = get_env("NOTION_PROP_STATUS", "Status")
        self.prop_url = get_env("NOTION_PROP_URL", "URL")
        self.prop_summary = get_env("NOTION_PROP_SUMMARY", "Summary")
        self.prop_confidence = get_env("NOTION_PROP_CONFIDENCE", "Confidence")
        self.prop_sensitive = get_env("NOTION_PROP_SENSITIVITY", "Sensitivity")

    def _simplify_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        url = props.get(self.prop_url, {}).get("url")
        status_prop = props.get(self.prop_status, {})
        status_name = None
        if "status" in status_prop and isinstance(status_prop["status"], dict):
            status_name = status_prop["status"].get("name")
        return {
            "id": page.get("id"),
            "url": url,
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
                        {"property": self.prop_status, "status": {"equals": "To Read"}},
                        {"property": self.prop_status, "status": {"equals": STATUS_PENDING}},
                        {"property": self.prop_status, "status": {"equals": STATUS_UNPROCESSED}},
                    ]
                },
            }
        )
        return [self._simplify_page(p) for p in resp.get("results", [])]

    def _update_status(self, page_id: str, status: str, extra_props: Optional[Dict[str, Any]] = None) -> None:
        props: Dict[str, Any] = {self.prop_status: {"status": {"name": status}}}
        if extra_props:
            props.update(extra_props)
        self.client.pages.update(page_id=page_id, properties=props)

    def mark_as_done(self, page_id: str, summary: str) -> None:
        props = {
            self.prop_summary: {"rich_text": [{"text": {"content": summary[:1900]}}]},
        }
        self._update_status(page_id, STATUS_READY, props)

    def mark_as_error(self, page_id: str, error: str) -> None:
        props = {
            self.prop_summary: {"rich_text": [{"text": {"content": f"Error: {error}"[:1900]}}]},
        }
        self._update_status(page_id, STATUS_ERROR, props)

    def mark_unprocessed(self, page_id: str, note: str) -> None:
        props = {
            self.prop_summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
        }
        self._update_status(page_id, STATUS_UNPROCESSED, props)

    def mark_excluded(self, page_id: str, note: str) -> None:
        props = {
            self.prop_summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
        }
        self._update_status(page_id, STATUS_EXCLUDED, props)

    def fetch_ready_for_digest(self, since: Optional[str], until: Optional[str]) -> List[Dict[str, Any]]:
        filters: List[Dict[str, Any]] = [
            {"property": self.prop_status, "status": {"equals": STATUS_READY}},
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
