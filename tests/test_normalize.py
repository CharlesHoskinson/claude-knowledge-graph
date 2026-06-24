# tests/test_normalize.py
import json, pathlib, jsonschema
import normalize

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "skills" / "compiling-graphify-wiki" / "schemas"

def _raw():
    return json.loads((ROOT / "fixtures" / "graph-tiny-raw.json").read_text(encoding="utf-8"))

def test_normalize_matches_schema_and_maps_fields():
    snap = normalize.normalize(_raw(), "snap-tiny", "2026-06-24T00:00:00Z")
    jsonschema.validate(snap, json.loads((SCHEMAS / "graphify-snapshot.schema.json").read_text(encoding="utf-8")))
    n1 = next(n for n in snap["nodes"] if n["id"] == "proof_outsourcing")
    assert n1["kind"] == "concept" and n1["entity_kind"] is None
    assert n1["title"] == "Proof Outsourcing"
    assert n1["source_ids"] == ["docs/protocol.md"]
    e1 = snap["edges"][0]
    assert e1["id"] == "e1" and e1["predicate"] == "requires"

def test_sources_derived_from_source_file():
    snap = normalize.normalize(_raw(), "snap-tiny", "2026-06-24T00:00:00Z")
    ids = {s["source_id"] for s in snap["sources"]}
    assert ids == {"docs/protocol.md", "docs/prover.md"}
    protocol = next(s for s in snap["sources"] if s["source_id"] == "docs/protocol.md")
    assert protocol["title"] == "docs-protocol"          # extension stripped, '/'→'-'
    assert protocol["uri"] == "https://example.org/protocol"

def test_communities_grouped_by_integer_attr():
    snap = normalize.normalize(_raw(), "snap-tiny", "2026-06-24T00:00:00Z")
    c1 = next(c for c in snap["communities"] if c["id"] == "c1")
    assert c1["title"] == "Community 1"
    assert sorted(c1["member_node_ids"]) == ["proof_outsourcing", "verification"]

def test_real_export_normalizes_without_error():
    raw = json.loads((ROOT / "fixtures" / "graph-sample.json").read_text(encoding="utf-8"))
    snap = normalize.normalize(raw, "snap-real", "2026-06-24T00:00:00Z")
    jsonschema.validate(snap, json.loads((SCHEMAS / "graphify-snapshot.schema.json").read_text(encoding="utf-8")))
    assert len(snap["nodes"]) == len(raw["nodes"])
    assert len(snap["edges"]) == len(raw["links"])
