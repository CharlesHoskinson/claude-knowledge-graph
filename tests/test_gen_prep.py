# tests/test_gen_prep.py
import json, pathlib, yaml
import prep

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "skills" / "generating-knowledge-graph"
ONT = yaml.safe_load((GEN / "fixtures" / "ontology-sample.yaml").read_text(encoding="utf-8"))

def test_worksheet_one_entry_per_chunk_with_prompts(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "doc.md").write_text("app imports db. app defines config.", encoding="utf-8")
    manifest = {"raw_dir": str(raw), "files": [{"path": "doc.md", "bytes": 30}]}
    ws = prep.build_worksheet(manifest, ONT, chunk_size=10000)
    assert len(ws) == 1                                   # one chunk
    e = ws[0]
    assert e["file"] == "doc.md" and e["chunk_index"] == 0
    assert e["entity_types"] == ["Module", "Symbol"]
    assert e["relation_types"] == ["imports", "defines"]
    assert "app imports db" in e["text"]
    assert "JSON" in e["entity_prompt"]                   # extract.entity_prompt content
    # A5: the worksheet prompt must carry each entity type's description, not just names,
    # and frame the task to include abstract concepts (not only proper nouns).
    assert "A source-code module or document unit." in e["entity_prompt"]
    assert "abstract concepts" in e["entity_prompt"]

def test_worksheet_aligns_with_backend_chunk_count(tmp_path):
    # the number of worksheet entries must equal the backend's chunk count for the file
    import chunk as chunker
    raw = tmp_path / "raw"; raw.mkdir()
    text = "x " * 200                                     # ~400 chars
    (raw / "big.md").write_text(text, encoding="utf-8")
    manifest = {"raw_dir": str(raw), "files": [{"path": "big.md", "bytes": 400}]}
    ws = prep.build_worksheet(manifest, ONT, chunk_size=100, overlap=20)
    assert len(ws) == len(chunker.chunk_text(text.strip(), 100, 20))
    assert [e["chunk_index"] for e in ws] == list(range(len(ws)))
