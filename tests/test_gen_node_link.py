# tests/test_gen_node_link.py
import json, pathlib, node_link
from base import GraphBackend

ROOT = pathlib.Path(__file__).resolve().parents[1]

def test_sample_graph_is_valid_node_link():
    g = json.loads((ROOT / "fixtures" / "graph-sample.json").read_text(encoding="utf-8"))
    assert node_link.validate_node_link(g) == []

def test_missing_link_target_is_invalid():
    g = {"nodes": [{"id": "a", "label": "A"}], "links": [{"source": "a", "relation": "r"}]}
    findings = node_link.validate_node_link(g)
    assert any(f["severity"] == "error" for f in findings)

def test_backend_interface_is_abstract():
    b = GraphBackend()
    try:
        b.generate({}, {}, "out.json")
        assert False, "base generate must raise"
    except NotImplementedError:
        pass
