from src.digest import build_digest


def test_build_digest_groups_and_cites():
    entries = [
        {"id": "1", "tags": ["news"], "title": "Item1", "summary": "s1"},
        {"id": "2", "tags": ["news"], "title": "Item2", "summary": "s2"},
        {"id": "3", "tags": ["tech"], "title": "Item3", "summary": "s3"},
    ]
    digest = build_digest(entries)
    assert len(digest["sections"]) == 3
    assert set(digest["citations"]) == {"1", "2", "3"}
    titles = [s["title"] for s in digest["sections"]]
    assert any(t.startswith("[news]") for t in titles)
    assert any(t.startswith("[tech]") for t in titles)

