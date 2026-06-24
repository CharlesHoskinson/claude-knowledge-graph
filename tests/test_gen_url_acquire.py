# tests/test_gen_url_acquire.py
import pathlib, acquire

def test_classify_url():
    assert acquire.classify_input("https://example.org/page") == "url"
    assert acquire.classify_input("http://example.org") == "url"

def test_acquire_url_uses_injected_fetcher(tmp_path):
    raw = tmp_path / "raw"
    def stub_fetcher(url, raw_dir):
        p = pathlib.Path(raw_dir) / "example.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# fetched\nfrom {url}\n", encoding="utf-8")
        return "example.md"
    manifest = acquire.acquire(["https://example.org/page"], str(raw), fetcher=stub_fetcher)
    assert (raw / "example.md").exists()
    entry = next(f for f in manifest["files"] if f["path"] == "example.md")
    assert entry.get("source") == "url" and entry.get("url") == "https://example.org/page"

def test_acquire_files_unchanged_when_no_url(tmp_path):
    src = tmp_path / "a.md"; src.write_text("hi", encoding="utf-8")
    raw = tmp_path / "raw"
    manifest = acquire.acquire([str(src)], str(raw))
    assert [f["path"] for f in manifest["files"]] == ["a.md"]

def test_pick_markdown_selects_md_among_noise():
    assert acquire._pick_markdown({"page.md", "img1.png", "assets"}) == "page.md"

def test_pick_markdown_raises_without_md():
    import pytest
    with pytest.raises(RuntimeError):
        acquire._pick_markdown({"img1.png", "data.json"})

def test_scrape_script_path_resolves():
    # the default URL fetcher must point at the real llm-wiki scrape.py
    assert acquire._LLM_WIKI_SCRAPE.exists(), acquire._LLM_WIKI_SCRAPE
