#!/usr/bin/env python3
"""Structural validation + llm-wiki lint gate for a compiled wiki."""
import argparse, json, sys, subprocess, pathlib, yaml

SCAFFOLD = {"_index", "index", "overview", "log"}

def _frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}

def _structural(wiki_root, ledger):
    findings = []
    known = {c["claim_id"] for c in ledger["claims"]}
    for p in (pathlib.Path(wiki_root) / "wiki").rglob("*.md"):
        if p.stem in SCAFFOLD:
            continue
        fm = _frontmatter(p.read_text(encoding="utf-8"))
        if fm is None or "type" not in fm:
            findings.append({"severity": "error", "category": "missing-frontmatter", "path": str(p)})
            continue
        for cid in fm.get("claim_ids", []) or []:
            if cid not in known:
                findings.append({"severity": "error", "category": "unknown-claim-id",
                                 "path": str(p), "claim_id": cid})
    return findings

def _lint(wiki_root, lint_path):
    # The lint script's exit code is authoritative: nonzero => findings (or the
    # lint itself errored). Trusting a parsed "(N) finding" count over the return
    # code silently passes a crashed/erroring lint, and discards stderr.
    proc = subprocess.run([sys.executable, lint_path, wiki_root], capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stdout + ("\n" + proc.stderr if proc.stderr else "")).strip()
        return [{"severity": "error", "category": "llm-wiki-lint",
                 "message": detail[-2000:]}]
    return []

def validate(wiki_root, ledger, lint_path):
    findings = _structural(wiki_root, ledger) + _lint(wiki_root, lint_path)
    return {"result": "fail" if findings else "pass", "findings": findings}

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--llm-wiki-lint", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    led = yaml.safe_load(open(a.ledger, encoding="utf-8").read())
    report = validate(a.wiki, led, a.llm_wiki_lint)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "pass" else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
