# tests/test_ledger.py
import json, pathlib, jsonschema, yaml
import ledger

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "skills" / "compiling-graphify-wiki" / "schemas"

def _snap():
    return json.loads((ROOT / "fixtures" / "snapshot-tiny.json").read_text(encoding="utf-8"))

def test_ledger_has_edge_and_community_claims():
    led = ledger.build_ledger(_snap(), "led-tiny")
    jsonschema.validate(led, json.loads((SCHEMAS / "claim-ledger.schema.json").read_text(encoding="utf-8")))
    types = [c["claim_type"] for c in led["claims"]]
    assert "edge" in types and "community_summary" in types
    assert "attribute" not in types

def test_claim_ids_sequential_and_deterministic():
    led = ledger.build_ledger(_snap(), "led-tiny")
    ids = [c["claim_id"] for c in led["claims"]]
    assert ids == [f"CLM-{i:04d}" for i in range(1, len(ids) + 1)]
    assert led == ledger.build_ledger(_snap(), "led-tiny")   # rebuild identical

def test_edge_claim_text_and_provenance():
    led = ledger.build_ledger(_snap(), "led-tiny")
    c = next(x for x in led["claims"] if x["claim_type"] == "edge" and x["node_id"] == "proof_outsourcing")
    assert c["text"] == "Proof Outsourcing requires Verification."
    assert c["status"] == "supported" and c["source_ids"] == ["docs/protocol.md"]
