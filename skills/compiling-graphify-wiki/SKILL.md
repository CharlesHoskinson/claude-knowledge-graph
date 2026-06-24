---
name: compiling-graphify-wiki
description: Compile a Graphify knowledge-graph export into an llm-wiki-format markdown wiki with claim-level provenance, then validate it against llm-wiki lint. Use when the user wants to turn a Graphify graph.json into a browsable, cited wiki.
allowed-tools: Read Grep Glob Bash(python *) Bash(python3 *)
---

# Compiling Graphify Wiki (Stage 1)

Run the deterministic pipeline. Paths use `${CLAUDE_SKILL_DIR}` so the commands
are independent of the current working directory:

1. `python ${CLAUDE_SKILL_DIR}/scripts/normalize.py --graph <raw.json> --out <snapshot.json>`
2. `python ${CLAUDE_SKILL_DIR}/scripts/ledger.py --snapshot <snapshot.json> --out <ledger.yaml>`
3. `python ${CLAUDE_SKILL_DIR}/scripts/compile.py --snapshot <snapshot.json> --ledger <ledger.yaml> --out <wiki-root> --date <YYYY-MM-DD>`
4. `python ${CLAUDE_SKILL_DIR}/scripts/validate.py --wiki <wiki-root> --ledger <ledger.yaml> --llm-wiki-lint ${CLAUDE_SKILL_DIR}/../llm-wiki/scripts/lint.py`
5. `python ${CLAUDE_SKILL_DIR}/scripts/apply.py --wiki <wiki-root> --message "compile graphify wiki"`  (only if validate passed)

`apply.py` (step 5) commits only when `<wiki-root>` is a standalone git repo (or
a fresh directory it can `git init`). If the wiki lives inside a larger repo it
refuses, so it never stages unrelated working-tree changes — commit it through
the enclosing repo yourself in that case.
