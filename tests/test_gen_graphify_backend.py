# tests/test_gen_graphify_backend.py
import json, pathlib, shutil
from graphify_backend import GraphifyBackend

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "fixtures" / "graph-sample.json"

def _fake_run_factory(raw_dir):
    # emulate `graphify extract`: write graph-sample.json to <raw_dir>/graphify-out/graph.json
    def fake_run(cmd, *a, **k):
        out = pathlib.Path(raw_dir) / "graphify-out"
        out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE, out / "graph.json")
        class R: returncode = 0; stdout = ""; stderr = ""
        return R()
    return fake_run

def test_graphify_backend_produces_valid_node_link(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    manifest = {"raw_dir": str(raw), "files": [{"path": "notes.md", "bytes": 10}]}
    out = tmp_path / "graph.json"
    backend = GraphifyBackend()
    graph = backend.generate(manifest, {}, str(out), run=_fake_run_factory(str(raw)))
    assert out.exists()
    assert len(graph["nodes"]) == 8 and len(graph["links"]) == 6
    import node_link
    assert node_link.validate_node_link(graph) == []

def test_graphify_backend_raises_when_no_graph_produced(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    manifest = {"raw_dir": str(raw), "files": []}
    def bad_run(cmd, *a, **k):
        class R: returncode = 1; stdout = ""; stderr = "boom"
        return R()
    try:
        GraphifyBackend().generate(manifest, {}, str(tmp_path / "g.json"), run=bad_run)
        assert False, "should raise when graphify produced no graph"
    except RuntimeError:
        pass
