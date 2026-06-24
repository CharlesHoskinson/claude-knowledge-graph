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

def test_lint_nonzero_exit_is_authoritative(tmp_path):
    # B5: validate must trust the lint return code, not a parsed "(N) finding"
    # count. A lint that exits 1 while printing "0 finding(s)." must still fail.
    snap = _snap(); led = ledger.build_ledger(snap, "led-tiny")
    out = tmp_path / "wiki-root"
    compiler.compile_wiki(snap, led, str(out), "2026-06-24")
    stub = tmp_path / "stub_lint.py"
    stub.write_text(
        "import sys\n"
        "print('0 finding(s).')\n"            # misleading stdout count
        "sys.stderr.write('boom: lint crashed\\n')\n"
        "sys.exit(1)\n",
        encoding="utf-8")
    report = validate.validate(str(out), led, str(stub))
    assert report["result"] == "fail"
    lint_findings = [f for f in report["findings"] if f["category"] == "llm-wiki-lint"]
    assert lint_findings, report["findings"]
    assert "boom" in lint_findings[0]["message"]


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
