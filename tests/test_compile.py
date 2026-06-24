# tests/test_compile.py
import json, pathlib
import compile as compiler, ledger

ROOT = pathlib.Path(__file__).resolve().parents[1]

def _snap():
    return json.loads((ROOT / "fixtures" / "snapshot-tiny.json").read_text(encoding="utf-8"))

def _build(tmp_path):
    snap = _snap()
    led = ledger.build_ledger(snap, "led-tiny")
    out = tmp_path / "wiki-root"
    compiler.compile_wiki(snap, led, str(out), "2026-06-24")
    return out

def test_pages_written_with_title_filenames(tmp_path):
    out = _build(tmp_path)
    assert (out / "wiki" / "concepts" / "Proof Outsourcing.md").exists()   # spaces, not kebab
    assert (out / "wiki" / "concepts" / "Verification.md").exists()
    assert (out / "wiki" / "concepts" / "Example Prover.md").exists()
    assert (out / "wiki" / "sources" / "docs-protocol.md").exists()
    assert (out / "wiki" / "maps" / "Community 1.md").exists()

def test_concept_claims_have_provenance(tmp_path):
    out = _build(tmp_path)
    page = (out / "wiki" / "concepts" / "Proof Outsourcing.md").read_text(encoding="utf-8")
    assert page.splitlines()[0] == "---" and "type: concept" in page
    claim_bullets = [l for l in page.splitlines() if l.startswith("- ")]
    assert claim_bullets
    assert all(("^[" in l) or ("[[" in l) for l in claim_bullets)

def test_pages_registered_in_category_index(tmp_path):
    out = _build(tmp_path)
    idx = (out / "wiki" / "concepts" / "_index.md").read_text(encoding="utf-8")
    assert "[[Proof Outsourcing]]" in idx

def test_no_title_collision_data_loss(tmp_path):
    import normalize
    raw = json.loads((ROOT / "fixtures" / "graph-real.json").read_text(encoding="utf-8"))
    snap = normalize.normalize(raw, "snap-real", "2026-06-24T00:00:00Z")
    led = ledger.build_ledger(snap, "led-real")
    out = tmp_path / "wiki-root"
    compiler.compile_wiki(snap, led, str(out), "2026-06-24")
    pages = list((out / "wiki" / "concepts").glob("*.md"))
    pages = [p for p in pages if p.stem != "_index"]
    assert len(pages) == len(snap["nodes"]), f"{len(pages)} pages != {len(snap['nodes'])} nodes (collision data loss)"
