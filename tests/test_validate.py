# tests/test_validate.py
import json, pathlib
import compile as compiler, ledger, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
LINT = ROOT / "skills" / "llm-wiki" / "scripts" / "lint.py"

def _snap():
    return json.loads((ROOT / "fixtures" / "snapshot-tiny.json").read_text(encoding="utf-8"))

def test_compiled_wiki_passes_validation(tmp_path):
    snap = _snap(); led = ledger.build_ledger(snap, "led-tiny")
    out = tmp_path / "wiki-root"
    compiler.compile_wiki(snap, led, str(out), "2026-06-24")
    report = validate.validate(str(out), led, str(LINT))
    assert report["result"] == "pass", report["findings"]

def test_unknown_claim_id_fails_validation(tmp_path):
    snap = _snap(); led = ledger.build_ledger(snap, "led-tiny")
    out = tmp_path / "wiki-root"
    compiler.compile_wiki(snap, led, str(out), "2026-06-24")
    p = out / "wiki" / "concepts" / "Verification.md"
    # inject a bogus claim id into frontmatter claim_ids (Verification has an empty list)
    txt = p.read_text(encoding="utf-8").replace("claim_ids: []", "claim_ids:\n- CLM-9999")
    p.write_text(txt, encoding="utf-8")
    report = validate.validate(str(out), led, str(LINT))
    assert report["result"] == "fail"
    assert any(f["category"] == "unknown-claim-id" for f in report["findings"])
