from typing import Any, Dict, List, Optional

from notion_client import Client

from src.utils import get_env


class NotionManager:
    def __init__(self) -> None:
        token = get_env("NOTION_TOKEN", required=True)
        self.database_id = get_env("NOTION_DATABASE_ID", required=True)
        self.client = Client(auth=token)

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        # Placeholder: query Notion DB for Status in ["To Read", "pending"]
        return []

    def mark_as_done(self, page_id: str, summary: str) -> None:
        # Placeholder: update page with summary/status
        return None

    def mark_as_error(self, page_id: str, error: str) -> None:
        # Placeholder: set status to Error and attach error message
        return None

    def fetch_ready_for_digest(self, since: Optional[str], until: Optional[str]) -> List[Dict[str, Any]]:
        # Placeholder for digest window filter
        return []
