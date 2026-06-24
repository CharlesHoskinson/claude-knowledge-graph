# tests/test_gen_ontology.py
import pathlib, ontology

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "ontology-sample.yaml"

def test_sample_ontology_is_valid():
    obj = ontology.load_ontology(str(SAMPLE))
    assert ontology.validate_ontology(obj) == []

def test_relation_missing_range_is_invalid():
    obj = {"ontology_id": "x",
           "entity_types": [{"name": "Module", "description": "m", "examples": []}],
           "relation_types": [{"name": "imports", "domain": "Module", "description": "d"}],
           "scope": {"include": [], "exclude": [], "granularity": "symbol"}}
    findings = ontology.validate_ontology(obj)
    assert any(f["severity"] == "error" for f in findings)

def test_relation_endpoint_must_be_declared_entity():
    obj = {"ontology_id": "x",
           "entity_types": [{"name": "Module", "description": "m", "examples": []}],
           "relation_types": [{"name": "imports", "domain": "Module", "range": "Ghost", "description": "d"}],
           "scope": {"include": [], "exclude": [], "granularity": "symbol"}}
    findings = ontology.validate_ontology(obj)
    assert any("Ghost" in f["message"] for f in findings)
