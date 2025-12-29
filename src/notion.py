from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from notion_client import Client
from notion_client.errors import APIResponseError

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
    title: str = "Name"
    status: str = "Status"
    url: str = "URL"
    summary: str = "Summary"
    raw_content: str = "Raw Content"
    reason: str = "Reason"  # audit/notes
    source: str = "Source"
    confidence: str = "Confidence"
    sensitivity: str = "Sensitivity"
    files: str = "Files"
    canonical_url: str = "Canonical URL"
    duplicate_of: str = "Duplicate Of"
    tags: str = "Tags"
    rule_version: str = "Rule Version"
    prompt_version: str = "Prompt Version"
    item_type: str = "ItemType"  # Select: url_resource, note_content, empty_invalid


class NotionManager:
    def __init__(self) -> None:
        token = get_env("NOTION_TOKEN", required=True)
        self.database_id = get_env("NOTION_DATABASE_ID", required=True)
        self.data_source_id = get_env("NOTION_DATA_SOURCE_ID", required=False)
        self.digest_parent_id = get_env("NOTION_DIGEST_PARENT_ID", required=False)
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
            title=get_env("NOTION_PROP_TITLE", PropertyNames.title),
            status=get_env("NOTION_PROP_STATUS", PropertyNames.status),
            url=get_env("NOTION_PROP_URL", PropertyNames.url),
            summary=get_env("NOTION_PROP_SUMMARY", PropertyNames.summary),
            raw_content=get_env("NOTION_PROP_RAW_CONTENT", PropertyNames.raw_content),
            reason=get_env("NOTION_PROP_REASON", PropertyNames.reason),
            source=get_env("NOTION_PROP_SOURCE", PropertyNames.source),
            confidence=get_env("NOTION_PROP_CONFIDENCE", PropertyNames.confidence),
            sensitivity=get_env("NOTION_PROP_SENSITIVITY", PropertyNames.sensitivity),
            files=get_env("NOTION_PROP_FILES", PropertyNames.files),
            canonical_url=get_env("NOTION_PROP_CANONICAL_URL", PropertyNames.canonical_url),
            duplicate_of=get_env("NOTION_PROP_DUPLICATE_OF", PropertyNames.duplicate_of),
            tags=get_env("NOTION_PROP_TAGS", PropertyNames.tags),
            rule_version=get_env("NOTION_PROP_RULE_VERSION", PropertyNames.rule_version),
            prompt_version=get_env("NOTION_PROP_PROMPT_VERSION", PropertyNames.prompt_version),
            item_type=get_env("NOTION_PROP_ITEM_TYPE", PropertyNames.item_type),
        )

    def has_page_blocks(self, page_id: str) -> bool:
        """
        Check if a page has content blocks.
        
        Uses page_size=1 to minimize API response.
        Filters out empty paragraphs to detect truly empty pages.
        
        Args:
            page_id: Notion page ID
            
        Returns:
            True if page has non-empty content blocks, False otherwise
        """
        if not page_id:
            return False
        try:
            resp = self.client.blocks.children.list(block_id=page_id, page_size=1)
            results = resp.get("results", [])
            if not results:
                return False
            # Check if content is meaningful (not just empty paragraphs)
            for block in results:
                block_type = block.get("type", "")
                # Non-paragraph blocks are considered content
                if block_type != "paragraph":
                    return True
                # Check if paragraph has text
                para = block.get("paragraph", {})
                rich_text = para.get("rich_text", [])
                if rich_text:
                    # Check if any text is non-empty
                    for rt in rich_text:
                        text = rt.get("plain_text", "") or rt.get("text", {}).get("content", "")
                        if text.strip():
                            return True
            # If we got here, results exist but all are empty paragraphs
            # However, if there's at least one result, Notion may have more blocks
            # For safety, treat any block response as "has content"
            return len(results) > 0
        except Exception:
            return False

    def _query(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Compat query helper for databases without .query convenience."""
        # Prefer data_source query if available; fallback to database query on invalid URL
        if self.data_source_id:
            ds_path = f"data_sources/{self.data_source_id}/query"
            try:
                return self.client.request(path=ds_path, method="post", body=body)
            except APIResponseError as exc:
                if exc.code == "invalid_request_url":
                    # Fallback to database query
                    pass
                else:
                    raise
        db_path = f"databases/{self.database_id}/query"
        return self.client.request(path=db_path, method="post", body=body)

    def _status_filter(self, name: str) -> Dict[str, Any]:
        """Use select filter to stay compatible with DBs whose Status is select."""
        return {"property": self.prop.status, "select": {"equals": name}}

    def _status_empty_filter(self) -> Dict[str, Any]:
        """Match rows with empty Status."""
        return {"property": self.prop.status, "select": {"is_empty": True}}

    def _simplify_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})
        url = props.get(self.prop.url, {}).get("url")
        files_prop = props.get(self.prop.files, {})
        title_prop = props.get(self.prop.title, {})
        summary_prop = props.get(self.prop.summary, {})
        raw_prop = props.get(self.prop.raw_content, {})
        source_prop = props.get(self.prop.source, {})
        attachments: List[str] = []
        if isinstance(files_prop, dict) and "files" in files_prop:
            for f in files_prop.get("files", []):
                ftype = f.get("type")
                if ftype and isinstance(f.get(ftype), dict):
                    link = f[ftype].get("url")
                    if link:
                        attachments.append(link)
        title_text = ""
        if isinstance(title_prop, dict):
            titems = title_prop.get("title", [])
            if titems:
                title_text = titems[0].get("plain_text", "") or titems[0].get("text", {}).get("content", "")
        summary_text = ""
        if isinstance(summary_prop, dict):
            sitems = summary_prop.get("rich_text", [])
            if sitems:
                summary_text = sitems[0].get("plain_text", "") or sitems[0].get("text", {}).get("content", "")
        raw_text = ""
        if isinstance(raw_prop, dict):
            ritems = raw_prop.get("rich_text", [])
            if ritems:
                raw_text = ritems[0].get("plain_text", "") or ritems[0].get("text", {}).get("content", "")
        source_value = ""
        if isinstance(source_prop, dict):
            sitems = source_prop.get("rich_text", [])
            if sitems:
                source_value = sitems[0].get("plain_text", "") or sitems[0].get("text", {}).get("content", "")

        tags_prop = props.get(self.prop.tags, {})
        tags: List[str] = []
        if isinstance(tags_prop, dict):
            for t in tags_prop.get("multi_select", []) or []:
                name = t.get("name")
                if name:
                    tags.append(name)

        source_value = ""
        if isinstance(source_prop, dict):
            sitems = source_prop.get("rich_text", [])
            if sitems:
                source_value = sitems[0].get("plain_text", "") or sitems[0].get("text", {}).get("content", "")

        status_prop = props.get(self.prop.status, {})
        status_name = None
        if "status" in status_prop and isinstance(status_prop["status"], dict):
            status_name = status_prop["status"].get("name")
        
        # Extract item_type
        item_type_prop = props.get(self.prop.item_type, {})
        item_type_value = None
        if isinstance(item_type_prop, dict) and "select" in item_type_prop:
            select_val = item_type_prop.get("select")
            if isinstance(select_val, dict):
                item_type_value = select_val.get("name")
        
        # Generate page link
        page_id = page.get("id", "")
        page_link = f"https://notion.so/{page_id.replace('-', '')}" if page_id else ""
        
        return {
            "id": page_id,
            "url": url,
            "attachments": attachments,
            "status": status_name,
            "title": title_text,
            "summary": summary_text,
            "tags": tags,
            "raw_content": raw_text,
            "source": source_value,
            "item_type": item_type_value,
            "page_link": page_link,
            "raw": page,
        }

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Fetch pages whose status is To Read/pending/unprocessed."""
        resp = self._query(
            {
                "filter": {
                    "or": [
                        self._status_filter(self.status.to_read),
                        self._status_filter(self.status.pending),
                        self._status_filter(self.status.unprocessed),
                        self._status_empty_filter(),
                    ]
                }
            }
        )
        return [self._simplify_page(p) for p in resp.get("results", [])]

    def find_by_canonical(self, canonical_url: str) -> Optional[Dict[str, Any]]:
        resp = self._query(
            {
                "filter": {
                    "property": self.prop.canonical_url,
                    "url": {"equals": canonical_url},
                }
            }
        )
        results = resp.get("results", [])
        if not results:
            return None
        return self._simplify_page(results[0])

    def _set_status(self, page_id: str, status: str, extra_props: Optional[Dict[str, Any]] = None) -> None:
        """Update status property; try Status type first, then fall back to select for compatibility."""
        base_props: Dict[str, Any] = extra_props.copy() if extra_props else {}
        # First attempt: Status type
        try:
            props = base_props.copy()
            props[self.prop.status] = {"status": {"name": status}}
            self.client.pages.update(page_id=page_id, properties=props)
            return
        except Exception:
            pass
        # Fallback: Select type
        props = base_props.copy()
        props[self.prop.status] = {"select": {"name": status}}
        self.client.pages.update(page_id=page_id, properties=props)

    def _update_status(self, page_id: str, status: str, extra_props: Optional[Dict[str, Any]] = None) -> None:
        self._set_status(page_id, status, extra_props)

    def _update_with_reason_fallback(self, page_id: str, props: Dict[str, Any]) -> None:
        try:
            self.client.pages.update(page_id=page_id, properties=props)
            return
        except APIResponseError as exc:
            if self.prop.reason in props and "property" in str(exc).lower() and "exists" in str(exc).lower():
                trimmed = {k: v for k, v in props.items() if k != self.prop.reason}
                self.client.pages.update(page_id=page_id, properties=trimmed)
                return
            raise

    def _with_reason(self, note: Optional[str], props: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        merged: Dict[str, Any] = props.copy() if props else {}
        if note:
            merged[self.prop.reason] = {"rich_text": [{"text": {"content": note[:1900]}}]}
        return merged

    # ================================================================
    # Block Helper Functions for Notion Page Content
    # ================================================================

    def _block_heading1(self, text: str) -> Dict[str, Any]:
        """Create a heading_1 block."""
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def _block_heading2(self, text: str) -> Dict[str, Any]:
        """Create a heading_2 block."""
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def _block_heading3(self, text: str) -> Dict[str, Any]:
        """Create a heading_3 block."""
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def _block_paragraph(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def _block_paragraph_with_link(self, text: str, url: str) -> Dict[str, Any]:
        """Create a paragraph block with a clickable link."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": text, "link": {"url": url}}}
                ]
            },
        }

    def _block_bullet(self, text: str) -> Dict[str, Any]:
        """Create a bulleted_list_item block."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
        }

    def _block_bullet_with_link(self, text: str, url: str) -> Dict[str, Any]:
        """Create a bulleted_list_item block with clickable link."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"type": "text", "text": {"content": text[:2000], "link": {"url": url}}}
                ]
            },
        }

    def _block_divider(self) -> Dict[str, Any]:
        """Create a divider block."""
        return {"object": "block", "type": "divider", "divider": {}}

    # ================================================================
    # Digest Page Creation
    # ================================================================

    def create_digest_page(
        self,
        title: str,
        digest_data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a digest page with ItemType-based structure.
        
        Args:
            title: Page title
            digest_data: Dict with 'overview', 'url_items', 'note_items', 'empty_items', 'citations'
            metadata: Optional metadata dict
            
        Returns:
            Created page ID or None
        """
        if not self.digest_parent_id:
            return None

        children_blocks: List[Dict[str, Any]] = []

        # Metadata line
        if metadata:
            meta_text = "📊 " + " | ".join(f"{k}: {v}" for k, v in metadata.items())
            children_blocks.append(self._block_paragraph(meta_text))

        # Overview section
        children_blocks.append(self._block_heading1("📋 综合概述"))
        overview = digest_data.get("overview", "")
        if overview:
            children_blocks.append(self._block_paragraph(overview))
        children_blocks.append(self._block_divider())

        # URL Items section (with full summaries)
        url_items = digest_data.get("url_items", [])
        if url_items:
            children_blocks.append(self._block_heading2(f"🔗 网页内容 ({len(url_items)}条)"))
            for item in url_items:
                # Item title with page link
                item_title = item.get("title", "无标题")
                page_link = item.get("page_link", "")
                if page_link:
                    children_blocks.append(self._block_paragraph_with_link(f"📌 {item_title}", page_link))
                else:
                    children_blocks.append(self._block_heading3(f"📌 {item_title}"))
                
                # Highlights as bullet list
                highlights = item.get("highlights", [])
                for h in highlights:
                    children_blocks.append(self._block_bullet(h))
                
                # Source URL
                url = item.get("url", "")
                if url:
                    children_blocks.append(self._block_paragraph_with_link(f"🌐 {url}", url))
            
            children_blocks.append(self._block_divider())

        # Note Items section (title + page_link only)
        note_items = digest_data.get("note_items", [])
        if note_items:
            children_blocks.append(self._block_heading2(f"📝 笔记内容 ({len(note_items)}条)"))
            for item in note_items:
                item_title = item.get("title", "无标题")
                page_link = item.get("page_link", "")
                if page_link:
                    children_blocks.append(self._block_bullet_with_link(item_title, page_link))
                else:
                    children_blocks.append(self._block_bullet(item_title))
            
            children_blocks.append(self._block_divider())

        # Empty Items section (title + page_link only)
        empty_items = digest_data.get("empty_items", [])
        if empty_items:
            children_blocks.append(self._block_heading2(f"⚠️ 待处理 ({len(empty_items)}条)"))
            for item in empty_items:
                item_title = item.get("title", "无标题")
                page_link = item.get("page_link", "")
                if page_link:
                    children_blocks.append(self._block_bullet_with_link(item_title, page_link))
                else:
                    children_blocks.append(self._block_bullet(item_title))
            
            children_blocks.append(self._block_divider())

        # Citations
        citations = digest_data.get("citations", [])
        citations_text = f"引用: {len(citations)}条" if citations else "引用: 无"
        children_blocks.append(self._block_paragraph(citations_text))

        page = self.client.pages.create(
            parent={"type": "page_id", "page_id": self.digest_parent_id},
            properties={
                "title": {"title": [{"text": {"content": title}}]},
            },
            children=children_blocks,
        )
        return page.get("id")

    def mark_as_done(self, page_id: str, summary: str, status: Optional[str] = None) -> None:
        props = {
            self.prop.summary: {"rich_text": [{"text": {"content": summary[:1900]}}]},
        }
        target_status = status or self.status.ready
        self._update_status(page_id, target_status, props)

    def mark_as_error(self, page_id: str, error: str) -> None:
        props = self._with_reason(
            error,
            {
                self.prop.summary: {"rich_text": [{"text": {"content": f"Error: {error}"[:1900]}}]},
            },
        )
        self._update_status(page_id, self.status.error, props)

    def mark_unprocessed(self, page_id: str, note: str) -> None:
        props = self._with_reason(
            note,
            {
                self.prop.summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
            },
        )
        self._update_status(page_id, self.status.unprocessed, props)

    def mark_excluded(self, page_id: str, note: str) -> None:
        props = self._with_reason(
            note,
            {
                self.prop.summary: {"rich_text": [{"text": {"content": note[:1900]}}]},
            },
        )
        self._update_status(page_id, self.status.excluded, props)

    def fetch_ready_for_digest(
        self,
        since: Optional[str],
        until: Optional[str],
        include_private: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch items ready for digest, with optional date window and sensitivity gating."""
        filters: List[Dict[str, Any]] = [
            self._status_filter(self.status.ready),
        ]
        if not include_private:
            filters.append({"property": self.prop.sensitivity, "select": {"does_not_equal": "private"}})

        if since or until:
            # Assume Created time for now; adjust to a date property if schema differs
            date_filter: Dict[str, Any] = {"timestamp": "created_time", "created_time": {}}
            if since:
                date_filter["created_time"]["on_or_after"] = since
            if until:
                date_filter["created_time"]["on_or_before"] = until
            filters.append(date_filter)

        resp = self._query({"filter": {"and": filters}})
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
        raw_content: Optional[str] = None,
        canonical_url: Optional[str] = None,
        source: Optional[str] = None,
    ) -> None:
        props: Dict[str, Any] = {
            self.prop.tags: {"multi_select": [{"name": t} for t in tags]},
            self.prop.sensitivity: {"select": {"name": sensitivity}},
            self.prop.confidence: {"number": confidence},
            self.prop.rule_version: {"rich_text": [{"text": {"content": rule_version}}]},
            self.prop.prompt_version: {"rich_text": [{"text": {"content": prompt_version}}]},
        }
        if raw_content:
            props[self.prop.raw_content] = {"rich_text": [{"text": {"content": raw_content[:1900]}}]}
        if canonical_url:
            props[self.prop.canonical_url] = {"url": canonical_url}
        if source:
            props[self.prop.source] = {"rich_text": [{"text": {"content": source[:1900]}}]}
        self.client.pages.update(page_id=page_id, properties=props)

    def set_title(self, page_id: str, title: str, note: Optional[str] = None) -> None:
        props: Dict[str, Any] = {
            self.prop.title: {"title": [{"text": {"content": title[:1900]}}]},
        }
        props = self._with_reason(note, props)
        self.client.pages.update(page_id=page_id, properties=props)

    def set_item_type(self, page_id: str, item_type: str) -> None:
        """
        Set the ItemType select field.
        
        Args:
            page_id: Notion page ID
            item_type: One of 'url_resource', 'note_content', 'empty_invalid'
        """
        props = {
            self.prop.item_type: {"select": {"name": item_type}},
        }
        self.client.pages.update(page_id=page_id, properties=props)

    def add_file_to_item(
        self,
        page_id: str,
        file_url: str,
        file_name: Optional[str] = None,
    ) -> bool:
        """
        Add an external file URL to the Files property.
        
        IMPORTANT: Notion API only supports publicly accessible HTTP/HTTPS URLs.
        Local file:// URLs will NOT work - they appear as broken images.
        
        For local screenshots, you must first upload to cloud storage (S3, R2, etc.)
        and use the returned public URL.
        
        Args:
            page_id: Notion page ID
            file_url: Public HTTP/HTTPS URL of the file
            file_name: Display name for the file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not file_url:
            return False
        
        # Validate URL - must be HTTP/HTTPS
        if not file_url.startswith(("http://", "https://")):
            logger.warning(
                f"Skipping file attachment: Notion only supports HTTP/HTTPS URLs. "
                f"Got: {file_url[:50]}... "
                f"Consider uploading to cloud storage first."
            )
            return False
        
        # Get display name from URL if not provided
        if not file_name:
            file_name = file_url.split("/")[-1].split("?")[0] or "file"
        
        try:
            # First, get existing files to preserve them
            page = self.client.pages.retrieve(page_id)
            existing_files = []
            files_prop = page.get("properties", {}).get(self.prop.files, {})
            if isinstance(files_prop, dict) and "files" in files_prop:
                for f in files_prop.get("files", []):
                    # Preserve existing file references
                    existing_files.append(f)
            
            # Add new file as external reference
            new_file = {
                "type": "external",
                "name": file_name,
                "external": {"url": file_url}
            }
            existing_files.append(new_file)
            
            # Update the Files property
            props = {
                self.prop.files: {"files": existing_files}
            }
            self.client.pages.update(page_id=page_id, properties=props)
            return True
            
        except Exception as e:
            logger.warning(f"Failed to add file to Notion: {e}")
            return False
