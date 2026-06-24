# tests/test_gen_llm_backend.py
import json, pathlib, yaml
import pytest
from llm_backend import LlmBackend
import llm_client, node_link

ROOT = pathlib.Path(__file__).resolve().parents[1]
ONT = yaml.safe_load((ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "ontology-sample.yaml").read_text(encoding="utf-8"))

def test_llm_backend_produces_typed_valid_clustered_graph(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "doc.md").write_text("app defines config. app imports db.", encoding="utf-8")
    manifest = {"raw_dir": str(raw), "files": [{"path": "doc.md", "bytes": 30}]}
    cass = llm_client.CassetteClient([
        {"entities": [{"name": "app", "type": "Module"}, {"name": "config", "type": "Symbol"},
                      {"name": "db", "type": "Module"}]},
        {"relations": [{"source": "app", "predicate": "defines", "target": "config"},
                       {"source": "app", "predicate": "imports", "target": "db"}]},
    ])
    out = tmp_path / "graph.json"
    graph = LlmBackend(cass, chunk_size=10000).generate(manifest, ONT, str(out))
    assert out.exists()
    assert node_link.validate_node_link(graph) == []
    assert all("type" in n and isinstance(n["community"], int) for n in graph["nodes"])   # typed + clustered
    labels = sorted(n["label"] for n in graph["nodes"])
    assert labels == ["app", "config", "db"]
    assert graph["directed"] is True and graph["hyperedges"] == []

def test_generate_registry_has_llm_factory():
    import generate
    assert "llm" in generate.BACKENDS and callable(generate.BACKENDS["llm"])


def _single_chunk_manifest(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "doc.md").write_text("app imports db.", encoding="utf-8")   # one chunk at 10000
    return {"raw_dir": str(raw), "files": [{"path": "doc.md", "bytes": 15}]}

def test_cassette_too_short_raises_clear_error(tmp_path):
    # A4: one chunk needs 2 responses; a 1-response cassette must fail loudly (not IndexError)
    manifest = _single_chunk_manifest(tmp_path)
    cass = llm_client.CassetteClient([{"entities": []}])
    with pytest.raises(ValueError) as ei:
        LlmBackend(cass, chunk_size=10000).generate(manifest, ONT, str(tmp_path / "g.json"))
    msg = str(ei.value)
    assert "expected 2" in msg and "got 1" in msg

def test_cassette_too_long_raises_clear_error(tmp_path):
    # A4: extras must not be silently ignored
    manifest = _single_chunk_manifest(tmp_path)
    cass = llm_client.CassetteClient([{"entities": []}, {"relations": []}, {"relations": []}])
    with pytest.raises(ValueError) as ei:
        LlmBackend(cass, chunk_size=10000).generate(manifest, ONT, str(tmp_path / "g.json"))
    assert "expected 2" in str(ei.value) and "got 3" in str(ei.value)
