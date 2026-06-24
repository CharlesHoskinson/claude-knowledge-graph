import scaffold

def test_scaffold_creates_discovery_contract(tmp_path):
    root = tmp_path / "wiki-root"
    scaffold.scaffold(str(root), "test domain", "2026-06-24")
    claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.splitlines()[0] == "<!-- llm-wiki: v1 -->"
    assert (root / "wiki").is_dir()
    for cat in ("sources", "entities", "concepts", "syntheses"):
        assert (root / "wiki" / cat / "_index.md").exists()
    assert (root / "wiki" / "overview.md").exists()
    assert (root / "wiki" / "maps" / ".gitkeep").exists()
    assert "<!-- llm-wiki: v1 -->" not in (root / "wiki" / "overview.md").read_text(encoding="utf-8")
