# tests/test_gen_graph_validate.py
import json, pathlib, yaml, graph_validate, ontology

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

def test_unknown_link_type_fails_when_present():
    g = _g()
    # give nodes types so the typed path is active, and inject a link with a bad type
    for n in g["nodes"]:
        n["type"] = "Module"
    g["links"][0]["type"] = "frobnicates"   # not an ontology relation_type
    rep = graph_validate.validate_graph(g, ontology.load_ontology(str(ONT)))
    assert rep["result"] == "fail"
    assert any(f["category"] == "unknown-type" for f in rep["findings"])


def test_domain_range_violation_warns_but_passes():
    # A6: 'defines' is Module->Symbol; a Module->Module 'defines' edge violates range.
    ont = ontology.load_ontology(str(ONT))
    src = {"id": "app_module", "label": "app", "type": "Module",
           "source_file": "doc.md", "source_location": "chunk-0", "community": 0}
    tgt = {"id": "db_module", "label": "db", "type": "Module",
           "source_file": "doc.md", "source_location": "chunk-0", "community": 0}
    g = {"directed": True, "multigraph": False, "graph": {},
         "nodes": [src, tgt],
         "links": [{"source": "app_module", "target": "db_module",
                    "relation": "defines", "type": "defines",
                    "source_file": "doc.md", "source_location": "chunk-0"}],
         "hyperedges": []}
    rep = graph_validate.validate_graph(g, ont)
    assert any(f["category"] == "relation-domain-range" and f["severity"] == "warning"
               for f in rep["findings"]), rep["findings"]
    assert rep["result"] == "warn"   # warning only, never fail


def test_empty_graph_warns_but_passes():
    # A8: an empty (blank-source) graph should warn, not silently pass.
    ont = ontology.load_ontology(str(ONT))
    g = {"directed": True, "multigraph": False, "graph": {},
         "nodes": [], "links": [], "hyperedges": []}
    rep = graph_validate.validate_graph(g, ont)
    assert any(f["category"] == "empty-graph" and f["severity"] == "warning"
               for f in rep["findings"]), rep["findings"]
    assert rep["result"] == "warn"
