---
name: generating-knowledge-graph
description: Build a knowledge graph (graph.json) from a raw source, steered by a brainstormed intent and a confirmed ontology, then hand it to compiling-graphify-wiki. Use when the user wants to construct a knowledge graph for a project from their own files/corpus and make it accessible to the wiki.
allowed-tools: Read Grep Glob Bash(python *) Bash(python3 *)
---

# Generating Knowledge Graph

Build a `graph.json` from a raw source, steered by a brainstormed intent and a confirmed
ontology, then hand it to `compiling-graphify-wiki`. Graphs are user-generated — this skill
ships no graphs.

## Procedure

1. **Capture intent.** Run `superpowers:brainstorming` to elicit what graph the user wants
   (domain, the questions it must answer, key entity/relation kinds, scope). Write the
   agreed intent to `intent.md`. Do not extract before intent is captured.

2. **Draft and confirm the ontology.** From the intent plus a sample of the source, write
   `ontology.yaml` (entity_types, relation_types with domain->range, scope). Validate it:
   `python scripts/ontology.py --ontology ontology.yaml`. Present it for the user to
   edit/confirm before extracting.

3. **Acquire the source.** Local files/globs or a directory:
   `python scripts/acquire.py --inputs <paths-or-dir> --raw raw/ --out manifest.json`.
   If the input is already a node-link `graph.json`, skip to step 5 (compile).

4. **Generate the graph.** `python scripts/generate.py --manifest manifest.json
   --ontology ontology.yaml --backend graphify --out graph.json --report report.json`.
   The `graphify` backend wraps the local Graphify extractor (Ollama). Graphify output is
   type-less, so ontology *types* are not enforced by this backend; the report flags
   missing provenance and node-link errors. Review `report.json`.

5. **Hand off to the wiki.** Pass `graph.json` to `compiling-graphify-wiki` (normalize ->
   ledger -> compile -> validate -> apply) to produce the LLM-accessible wiki.

## Notes
- Live Graphify extraction needs the local Ollama backend; see graphify-local-run.
- The `llm` backend and URL acquisition arrive in G2; model defaults: local
  `qwen2.5-32b-instruct` (non-thinking, temp 0, JSON schema), API Claude Haiku 4.5 /
  Sonnet 4.6 (structured outputs, thinking off).

## Claude-native extraction (no Ollama, no API key)

Use this when running inside Claude Code — Claude is the extractor.

1. `python scripts/acquire.py --inputs <files-or-dir> --raw raw/ --out manifest.json`
2. `python scripts/prep.py --manifest manifest.json --ontology ontology.yaml --out worksheet.json --chunk-size 1200 --overlap 150`
3. Read `worksheet.json`. For EACH entry IN ORDER, perform two-stage extraction and append
   TWO objects to `responses.json` (a flat JSON array):
   - first `{"entities": [{"name","type"}, ...]}` — only `entity_types` from the entry, drawn from `text`;
   - then `{"relations": [{"source","predicate","target"}, ...]}` — only `relation_types`, endpoints among the entities you just listed. The `source` and `target` values MUST use the exact `name` strings from the entities you listed in stage 1 of the SAME chunk — mismatched endpoint names are silently dropped.
   The array MUST have exactly two objects per worksheet entry, in worksheet order (the
   backend re-chunks with the same `--chunk-size`/`--overlap`, so order and count must match).
4. `python scripts/generate.py --manifest manifest.json --ontology ontology.yaml --backend llm --cassette responses.json --chunk-size 1200 --overlap 150 --out graph.json --report report.json`
5. Hand `graph.json` to `compiling-graphify-wiki` (normalize → ledger → compile).

The Ollama adapter (`--backend llm` without `--cassette`) remains the headless fallback.
