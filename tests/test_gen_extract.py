# tests/test_gen_extract.py
import pathlib
import extract, llm_client

ROOT = pathlib.Path(__file__).resolve().parents[1]
import yaml
ONT = yaml.safe_load((ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "ontology-sample.yaml").read_text(encoding="utf-8"))

def test_slug_is_deterministic_and_type_qualified():
    assert extract.slug("App Config", "Symbol") == "app_config_symbol"
    assert extract.slug("config", "Symbol") != extract.slug("config", "Module")

def test_two_stage_extract_builds_typed_graph_and_filters_to_ontology():
    # cassette: stage A entities (one has an unknown type -> dropped), stage B relations
    cass = llm_client.CassetteClient([
        {"entities": [{"name": "app", "type": "Module"},
                      {"name": "config", "type": "Symbol"},
                      {"name": "noise", "type": "Bogus"}]},          # Bogus not in ontology -> dropped
        {"relations": [{"source": "app", "predicate": "defines", "target": "config"},
                       {"source": "app", "predicate": "frobnicates", "target": "config"},  # bad predicate -> dropped
                       {"source": "app", "predicate": "imports", "target": "ghost"}]},      # ghost not an entity -> dropped
    ])
    g = extract.extract_graph("some text", ONT, cass, source_file="doc.md", chunk_size=10000)
    ids = sorted(n["id"] for n in g["nodes"])
    assert ids == ["app_module", "config_symbol"]                    # Bogus dropped
    assert all(n.get("type") in {"Module", "Symbol"} for n in g["nodes"])
    assert all(n["source_file"] == "doc.md" for n in g["nodes"])
    assert len(g["links"]) == 1                                      # only app-defines-config survives
    link = g["links"][0]
    assert link["source"] == "app_module" and link["target"] == "config_symbol"
    assert link["relation"] == "defines" and link["type"] == "defines"

def test_entities_deduped_across_chunks():
    cass = llm_client.CassetteClient([
        {"entities": [{"name": "app", "type": "Module"}]},          # chunk 0 entities
        {"relations": []},                                          # chunk 0 relations
        {"entities": [{"name": "app", "type": "Module"}]},          # chunk 1 entities (dup)
        {"relations": []},                                          # chunk 1 relations
    ])
    text = "x" * 25                                                 # forces 2 chunks at size 20/overlap 5
    g = extract.extract_graph(text, ONT, cass, source_file="doc.md", chunk_size=20, overlap=5)
    assert [n["id"] for n in g["nodes"]] == ["app_module"]          # deduped to one
