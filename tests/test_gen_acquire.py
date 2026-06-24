import pathlib, acquire

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "source-sample"

def test_classify_dir_and_file_and_graph(tmp_path):
    assert acquire.classify_input(str(SRC)) == "dir"
    assert acquire.classify_input(str(SRC / "notes.md")) == "file"
    g = tmp_path / "g.json"
    g.write_text('{"nodes": [], "links": []}', encoding="utf-8")
    assert acquire.classify_input(str(g)) == "graph"

def test_acquire_stages_directory(tmp_path):
    raw = tmp_path / "raw"
    manifest = acquire.acquire([str(SRC)], str(raw))
    names = sorted(f["path"] for f in manifest["files"])
    assert names == ["api.md", "notes.md"]
    assert (raw / "notes.md").exists()
    assert all(f["bytes"] > 0 for f in manifest["files"])
