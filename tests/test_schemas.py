# tests/test_schemas.py
import json, pathlib, jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "skills" / "compiling-graphify-wiki" / "schemas"

def _schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))

def test_snapshot_schema_accepts_minimal_valid():
    snap = {"snapshot_id": "s", "created_at": "2026-06-24T00:00:00Z",
            "nodes": [{"id": "n1", "kind": "concept", "title": "T"}],
            "edges": [], "sources": [], "communities": []}
    jsonschema.validate(snap, _schema("graphify-snapshot.schema.json"))

def test_snapshot_schema_rejects_bad_kind():
    snap = {"snapshot_id": "s", "created_at": "2026-06-24T00:00:00Z",
            "nodes": [{"id": "n1", "kind": "bogus", "title": "T"}],
            "edges": [], "sources": [], "communities": []}
    try:
        jsonschema.validate(snap, _schema("graphify-snapshot.schema.json"))
        assert False, "should have rejected bad kind"
    except jsonschema.ValidationError:
        pass

def test_ledger_schema_accepts_minimal_valid():
    led = {"ledger_id": "l", "graph_snapshot_id": "s", "created_at": "2026-06-24T00:00:00Z",
           "claims": [{"claim_id": "CLM-0001", "text": "x", "claim_type": "edge",
                       "status": "supported", "graphify_nodes": ["n1"], "graphify_edges": ["e1"],
                       "source_ids": ["docs/protocol.md"], "contradicts": []}]}
    jsonschema.validate(led, _schema("claim-ledger.schema.json"))
