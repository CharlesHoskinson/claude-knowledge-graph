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


def test_acquire_same_basename_from_different_dirs_no_collision(tmp_path):
    # A2: two inputs named x.md from different dirs must stage to distinct files and
    # produce two distinct manifest paths with both contents preserved.
    d1 = tmp_path / "a"; d1.mkdir()
    d2 = tmp_path / "b"; d2.mkdir()
    (d1 / "x.md").write_text("from-a", encoding="utf-8")
    (d2 / "x.md").write_text("from-b-longer", encoding="utf-8")
    raw = tmp_path / "raw"
    manifest = acquire.acquire([str(d1 / "x.md"), str(d2 / "x.md")], str(raw))
    paths = [f["path"] for f in manifest["files"]]
    assert len(paths) == 2
    assert len(set(paths)) == 2                       # distinct manifest entries
    contents = {(raw / p).read_text(encoding="utf-8") for p in paths}
    assert contents == {"from-a", "from-b-longer"}    # both inputs preserved on disk
