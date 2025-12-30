from src.notion import NotionManager


def test_notion_manager_imports(monkeypatch):
    monkeypatch.setenv("NOTION_TOKEN", "dummy")
    monkeypatch.setenv("NOTION_ITEM_DB_ID", "dummy")
    nm = NotionManager()
    assert nm is not None
