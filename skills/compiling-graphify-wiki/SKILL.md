---
name: compiling-graphify-wiki
description: Compile a Graphify knowledge-graph export into an llm-wiki-format markdown wiki with claim-level provenance, then validate it against llm-wiki lint. Use when the user wants to turn a Graphify graph.json into a browsable, cited wiki.
allowed-tools: Read Grep Glob Bash(python *) Bash(python3 *)
---

# Compiling Graphify Wiki (Stage 1)

Run the deterministic pipeline:

1. `python scripts/normalize.py --graph <raw.json> --out <snapshot.json>`
2. `python scripts/ledger.py --snapshot <snapshot.json> --out <ledger.yaml>`
3. `python scripts/compile.py --snapshot <snapshot.json> --ledger <ledger.yaml> --out <wiki-root> --date <YYYY-MM-DD>`
4. `python scripts/validate.py --wiki <wiki-root> --ledger <ledger.yaml> --llm-wiki-lint ../llm-wiki/scripts/lint.py`
5. `python scripts/apply.py --wiki <wiki-root> --message "compile graphify wiki"`  (only if validate passed)
