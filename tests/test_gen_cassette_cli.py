# tests/test_gen_cassette_cli.py
import json, os, pathlib, subprocess, sys, yaml
import generate, node_link

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "skills" / "generating-knowledge-graph"


def test_generate_runs_standalone_without_pythonpath():
    # A3: generate.py must self-bootstrap sys.path so `python scripts/generate.py` works
    # with no PYTHONPATH (it imports siblings from scripts/ and scripts/backends/).
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    proc = subprocess.run([sys.executable, str(GEN / "scripts" / "generate.py"), "--help"],
                          capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr

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


def test_generate_report_surfaces_relation_drops(tmp_path):
    # A1: relations dropped during extraction appear in report.json with a warning finding
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "doc.md").write_text("app imports db.", encoding="utf-8")
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps({"raw_dir": str(raw), "files": [{"path": "doc.md", "bytes": 15}]}), encoding="utf-8")
    cassette = tmp_path / "responses.json"
    cassette.write_text(json.dumps([
        {"entities": [{"name": "app", "type": "Module"}, {"name": "db", "type": "Module"}]},
        {"relations": [{"source": "app", "predicate": "imports", "target": "db"},
                       {"source": "app", "predicate": "frobnicates", "target": "db"}]},  # dropped predicate
    ]), encoding="utf-8")
    ont = str(GEN / "fixtures" / "ontology-sample.yaml")
    out = tmp_path / "graph.json"; rep = tmp_path / "rep.json"
    rc = generate.main(["--manifest", str(manifest), "--ontology", ont, "--backend", "llm",
                        "--cassette", str(cassette), "--out", str(out), "--report", str(rep),
                        "--chunk-size", "10000"])
    assert rc == 0
    report = json.loads(rep.read_text(encoding="utf-8"))
    assert report["relation_drops"]["total"] == 1
    assert report["relation_drops"]["by_reason"]["unknown_predicate"] == 1
    assert any(f["category"] == "relation-drops" and f["severity"] == "warning" for f in report["findings"])
