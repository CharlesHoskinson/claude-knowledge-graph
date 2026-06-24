# tests/test_gen_cassette_cli.py
import json, pathlib, yaml
import generate, node_link

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "skills" / "generating-knowledge-graph"

def test_generate_cassette_cli_assembles_graph(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "doc.md").write_text("app imports db.", encoding="utf-8")
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"raw_dir": str(raw), "files": [{"path": "doc.md", "bytes": 15}]}), encoding="utf-8")
    cassette = tmp_path / "responses.json"
    cassette.write_text(json.dumps([
        {"entities": [{"name": "app", "type": "Module"}, {"name": "db", "type": "Module"}]},
        {"relations": [{"source": "app", "predicate": "imports", "target": "db"}]},
    ]), encoding="utf-8")
    ont = str(GEN / "fixtures" / "ontology-sample.yaml")
    out = tmp_path / "graph.json"; rep = tmp_path / "rep.json"
    rc = generate.main(["--manifest", str(manifest), "--ontology", ont, "--backend", "llm",
                        "--cassette", str(cassette), "--out", str(out), "--report", str(rep),
                        "--chunk-size", "10000"])
    assert rc == 0
    graph = json.loads(out.read_text(encoding="utf-8"))
    assert node_link.validate_node_link(graph) == []
    assert sorted(n["label"] for n in graph["nodes"]) == ["app", "db"]
    assert len(graph["links"]) == 1
