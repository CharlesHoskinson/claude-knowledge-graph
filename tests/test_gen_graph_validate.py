# tests/test_gen_graph_validate.py
import json, pathlib, graph_validate, ontology

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "fixtures" / "graph-sample.json"
ONT = ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "ontology-sample.yaml"

def _g():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))

def test_typeless_graph_passes_with_provenance():
    rep = graph_validate.validate_graph(_g(), ontology.load_ontology(str(ONT)))
    assert rep["result"] == "pass", rep["findings"]

def test_missing_provenance_warns():
    g = _g()
    del g["nodes"][0]["source_file"]
    rep = graph_validate.validate_graph(g, ontology.load_ontology(str(ONT)))
    assert rep["result"] in ("warn", "fail")
    assert any(f["category"] == "missing-provenance" for f in rep["findings"])

def test_unknown_node_type_fails_when_types_present():
    g = _g()
    g["nodes"][0]["type"] = "Ghost"   # not in ontology entity_types
    rep = graph_validate.validate_graph(g, ontology.load_ontology(str(ONT)))
    assert rep["result"] == "fail"
    assert any(f["category"] == "unknown-type" for f in rep["findings"])

def test_missing_provenance_yields_exactly_warn():
    g = _g()
    del g["nodes"][0]["source_location"]   # one node loses provenance; no type errors -> warn (not fail)
    rep = graph_validate.validate_graph(g, ontology.load_ontology(str(ONT)))
    assert rep["result"] == "warn", rep["findings"]
