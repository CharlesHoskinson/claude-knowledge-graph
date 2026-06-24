# tests/test_integration.py
import json, pathlib, subprocess, sys
import normalize, ledger, compile as compiler, validate, apply

ROOT = pathlib.Path(__file__).resolve().parents[1]
LINT = ROOT / "skills" / "llm-wiki" / "scripts" / "lint.py"

def _compile(raw_path, tmp_path, sid):
    raw = json.loads((ROOT / "fixtures" / raw_path).read_text(encoding="utf-8"))
    snap = normalize.normalize(raw, sid, "2026-06-24T00:00:00Z")
    led = ledger.build_ledger(snap, "led")
    out = tmp_path / "wiki-root"
    compiler.compile_wiki(snap, led, str(out), "2026-06-24")
    return out, led

def test_tiny_graph_compiles_to_lint_clean_wiki(tmp_path):
    out, led = _compile("graph-tiny-raw.json", tmp_path, "snap-tiny")
    proc = subprocess.run([sys.executable, str(LINT), str(out)], capture_output=True, text=True)
    assert "0 finding(s)." in proc.stdout, proc.stdout
    assert validate.validate(str(out), led, str(LINT))["result"] == "pass"
    apply.apply(str(out), "compile graphify wiki")
    log = subprocess.run(["git", "-C", str(out), "log", "--oneline"], capture_output=True, text=True)
    assert "compile graphify wiki" in log.stdout

def test_real_export_compiles_to_lint_clean_wiki(tmp_path):
    out, led = _compile("graph-sample.json", tmp_path, "snap-real")
    proc = subprocess.run([sys.executable, str(LINT), str(out)], capture_output=True, text=True)
    assert "0 finding(s)." in proc.stdout, proc.stdout[-3000:]

def test_apply_raises_on_empty_commit(tmp_path):
    import pytest
    out, led = _compile("graph-tiny-raw.json", tmp_path, "snap-tiny")
    apply.apply(str(out), "first commit")          # succeeds
    with pytest.raises(RuntimeError):
        apply.apply(str(out), "nothing to commit")  # no changes -> git commit fails -> raise
