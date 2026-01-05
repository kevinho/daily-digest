"""
Notion manager for the Reporting database.
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from notion_client import Client
from notion_client.errors import APIResponseError

from src.utils import get_env
from src.reporting.models import ReportData

logger = logging.getLogger(__name__)


class ReportingDBManager:
    """
    Manages the Reporting database in Notion.
    
    This database stores all generated reports (Daily, Weekly, Monthly).
    """
    
    # Notion API limit for children blocks per request
    BATCH_SIZE = 100
    
    def __init__(self) -> None:
        """Initialize the Reporting DB manager."""
        token = get_env("NOTION_TOKEN", required=True)
        self.database_id = get_env("NOTION_REPORTING_DB_ID", required=True)
        self.data_source_id = get_env("NOTION_REPORTING_DS_ID", required=False)
        self.client = Client(auth=token)
        
        # Property names (can be made configurable via env vars if needed)
        self.prop_title = "Name"
        self.prop_type = "Type"
        self.prop_date = "Date"
        self.prop_period_end = "Period End"
        self.prop_source_reports = "Source Reports"
        self.prop_source_items = "Source Items"
        self.prop_summary = "Summary"
        self.prop_highlights = "Highlights"
        self.prop_status = "Status"
    
    def _query(self, filter_obj: Dict[str, Any], sorts: List[Dict] = None) -> List[Dict]:
        """
        Query the Reporting database.
        
        Prioritizes data_source query if available, falls back to database query.
        """
        body: Dict[str, Any] = {"filter": filter_obj}
        if sorts:
            body["sorts"] = sorts
        
        # Try data_source query first if available
        if self.data_source_id:
            ds_path = f"data_sources/{self.data_source_id}/query"
            try:
                response = self.client.request(path=ds_path, method="post", body=body)
                return response.get("results", [])
            except APIResponseError as exc:
                if exc.code == "invalid_request_url":
                    # Fallback to database query
                    pass
                else:
                    raise
        
        # Use database query via client.request()
        db_path = f"databases/{self.database_id}/query"
        response = self.client.request(path=db_path, method="post", body=body)
        return response.get("results", [])
    
    def find_report(
        self,
        report_type: str,
        start_date: date,
    ) -> Optional[Dict[str, Any]]:
        """
        Find an existing report by type and start date.
        
        Args:
            report_type: "Daily", "Weekly", or "Monthly"
            start_date: Period start date
            
        Returns:
            Report dict if found, None otherwise
        """
        filter_obj = {
            "and": [
                {
                    "property": self.prop_type,
                    "select": {"equals": report_type},
                },
                {
                    "property": self.prop_date,
                    "date": {"equals": start_date.isoformat()},
                },
            ]
        }
        
        results = self._query(filter_obj)
        if results:
            return self._simplify_report(results[0])
        return None
    
    def query_reports_in_range(
        self,
        report_type: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Query reports of a given type within a date range.
        
        Args:
            report_type: "Daily", "Weekly", or "Monthly"
            start_date: Range start (inclusive)
            end_date: Range end (inclusive)
            
        Returns:
            List of report dicts, sorted by date ascending
        """
        filter_obj = {
            "and": [
                {
                    "property": self.prop_type,
                    "select": {"equals": report_type},
                },
                {
                    "property": self.prop_date,
                    "date": {"on_or_after": start_date.isoformat()},
                },
                {
                    "property": self.prop_date,
                    "date": {"on_or_before": end_date.isoformat()},
                },
            ]
        }
        
        sorts = [{"property": self.prop_date, "direction": "ascending"}]
        
        results = self._query(filter_obj, sorts)
        return [self._simplify_report(r) for r in results]
    
    def create_report(
        self,
        report_data: ReportData,
        source_item_ids: List[str] = None,
        source_report_ids: List[str] = None,
    ) -> Optional[str]:
        """
        Create a new report page in the Reporting database.
        
        Args:
            report_data: The report data to create
            source_item_ids: List of Inbox item IDs (for daily reports)
            source_report_ids: List of report IDs (for weekly/monthly)
            
        Returns:
            Created page ID or None on failure
        """
        # Build properties
        properties: Dict[str, Any] = {
            "title": {"title": [{"text": {"content": report_data.period.title}}]},
            self.prop_type: {"select": {"name": report_data.period.type.value}},
            self.prop_date: {"date": {"start": report_data.period.start_date.isoformat()}},
            self.prop_period_end: {"date": {"start": report_data.period.end_date.isoformat()}},
            self.prop_status: {"select": {"name": "published"}},
        }
        
        # Add summary if available
        if report_data.overview:
            properties[self.prop_summary] = {
                "rich_text": [{"text": {"content": report_data.overview[:2000]}}]
            }
        
        # Add highlights as multi-select
        if report_data.highlights:
            properties[self.prop_highlights] = {
                "multi_select": [{"name": h[:100]} for h in report_data.highlights[:10]]
            }
        
        # Add relations
        if source_item_ids:
            logger.info(f"Setting Source Items relation with {len(source_item_ids)} items: {source_item_ids[:3]}...")
            properties[self.prop_source_items] = {
                "relation": [{"id": id_} for id_ in source_item_ids]
            }
        else:
            logger.warning("No source_item_ids provided for report")
        
        if source_report_ids:
            logger.info(f"Setting Source Reports relation with {len(source_report_ids)} reports: {source_report_ids[:3]}...")
            properties[self.prop_source_reports] = {
                "relation": [{"id": id_} for id_ in source_report_ids]
            }
        
        # Content blocks
        children_blocks = report_data.content_blocks or []
        
        # Handle Notion's 100 block limit
        first_batch = children_blocks[:self.BATCH_SIZE]
        remaining = children_blocks[self.BATCH_SIZE:]
        
        try:
            # Create page with first batch of blocks
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=first_batch,
            )
            page_id = page.get("id")
            
            # Append remaining blocks in batches
            if page_id and remaining:
                for i in range(0, len(remaining), self.BATCH_SIZE):
                    batch = remaining[i : i + self.BATCH_SIZE]
                    self.client.blocks.children.append(block_id=page_id, children=batch)
            
            return page_id
            
        except APIResponseError as e:
            logger.error(f"Failed to create report: {e}")
            return None
    
    def _simplify_report(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key fields from a Notion page."""
        props = page.get("properties", {})
        
        # Extract title
        title_prop = props.get("title") or props.get(self.prop_title) or {}
        title_arr = title_prop.get("title", [])
        title = title_arr[0].get("plain_text", "") if title_arr else ""
        
        # Extract type
        type_prop = props.get(self.prop_type, {})
        type_select = type_prop.get("select") or {}
        report_type = type_select.get("name", "")
        
        # Extract date
        date_prop = props.get(self.prop_date, {})
        date_obj = date_prop.get("date") or {}
        date_str = date_obj.get("start", "")
        
        # Extract summary
        summary_prop = props.get(self.prop_summary, {})
        summary_arr = summary_prop.get("rich_text", [])
        summary = summary_arr[0].get("plain_text", "") if summary_arr else ""
        
        # Extract highlights
        highlights_prop = props.get(self.prop_highlights, {})
        highlights_arr = highlights_prop.get("multi_select", [])
        highlights = [h.get("name", "") for h in highlights_arr]
        
        return {
            "id": page.get("id"),
            "title": title,
            "type": report_type,
            "date": date_str,
            "summary": summary,
            "highlights": highlights,
            "url": page.get("url", ""),
        }

