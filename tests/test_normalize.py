# tests/test_normalize.py
import json, pathlib, subprocess, sys, jsonschema
import normalize
import compile as compiler, ledger

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

LINT = ROOT / "skills" / "llm-wiki" / "scripts" / "lint.py"


def test_edge_only_source_is_normalized_and_compiled():
    # B4: an EDGE carries a source_file that NO node cites. That source must still
    # appear in snapshot["sources"], compile must emit its source page, the citing
    # concept's claim footnote must link to it, and llm-wiki lint must be clean.
    raw = {
        "directed": True, "multigraph": False, "graph": {},
        "nodes": [
            {"id": "a", "label": "Alpha", "community": 1},
            {"id": "b", "label": "Beta", "community": 1},
        ],
        "links": [
            {"relation": "relates-to", "source": "a", "target": "b",
             "source_file": "edge_only.md", "source_url": "https://x/edge",
             "source_location": "L1"},
        ],
        "hyperedges": [],
    }
    snap = normalize.normalize(raw, "snap-edge", "2026-06-24T00:00:00Z")
    src_ids = {s["source_id"] for s in snap["sources"]}
    assert "edge_only.md" in src_ids, "edge-only source missing from snapshot sources"

    led = ledger.build_ledger(snap, "led-edge")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / "wiki-root"
        compiler.compile_wiki(snap, led, str(out), "2026-06-24")
        # source page exists (title strips .md -> "edge_only")
        assert (out / "wiki" / "sources" / "edge_only.md").exists()
        # the citing concept (edge source = node "a"/"Alpha") footnote links the source
        alpha = (out / "wiki" / "concepts" / "Alpha.md").read_text(encoding="utf-8")
        assert "[[edge_only]]" in alpha, alpha
        # nice-to-have: declared provenance in frontmatter matches the footnote
        assert "sources:" in alpha
        proc = subprocess.run([sys.executable, str(LINT), str(out)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr


def test_real_export_normalizes_without_error():
    raw = json.loads((ROOT / "fixtures" / "graph-sample.json").read_text(encoding="utf-8"))
    snap = normalize.normalize(raw, "snap-real", "2026-06-24T00:00:00Z")
    jsonschema.validate(snap, json.loads((SCHEMAS / "graphify-snapshot.schema.json").read_text(encoding="utf-8")))
    assert len(snap["nodes"]) == len(raw["nodes"])
    assert len(snap["edges"]) == len(raw["links"])
