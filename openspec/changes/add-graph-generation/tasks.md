## 1. G1 — Generation core (graphify backend, files/dir)

- [ ] 1.1 Scaffold `skills/generating-knowledge-graph/` (SKILL.md, scripts/, schemas/, fixtures/, tests/) and register it in `.claude-plugin/plugin.json`
- [ ] 1.2 Purge `fixtures/graph-real.json` (LCP-derived) from the working tree and from git history; add a synthetic, general-purpose node-link fixture and repoint the existing real-data tests to it
- [ ] 1.3 Define `ontology.yaml` schema (entity_types, relation_types with domain→range, scope) + a JSON/YAML schema and validation test
- [ ] 1.4 Implement intent capture: run `superpowers:brainstorming` and persist `intent.md` (skill-level procedure in SKILL.md; helper to record/locate the artifact)
- [ ] 1.5 Implement ontology drafting from intent + source sample, with a confirm/edit gate (deterministic scaffold + tests on a fixture intent)
- [ ] 1.6 Implement source acquisition for local files/globs and a directory/corpus → staged `raw/` (tests)
- [ ] 1.7 Define the `GraphBackend.generate(source, ontology, out_path)` interface + a shared node-link output validator reused from `compiling-graphify-wiki` (tests)
- [ ] 1.8 Implement the `graphify` backend: shell out to the installed CLI with ontology-as-guidance, post-filter to ontology types, emit node-link `graph.json` (tests; live extraction marker-gated)
- [ ] 1.9 Implement graph-vs-ontology validation (schema, type coverage, provenance) + gap report (tests)
- [ ] 1.10 Implement handoff: produced `graph.json` + `ontology.yaml` + report feed `compiling-graphify-wiki`; end-to-end test synthetic source + ontology → graph → compile → `llm-wiki lint` 0 findings

## 2. G2 — LLM backend and URL acquisition

- [ ] 2.1 `chunk.py`: deterministic source chunking (size + overlap), unit-tested
- [ ] 2.2 `llm_client.py`: `complete_json(prompt, schema) -> dict` interface; Ollama adapter (`qwen2.5-32b-instruct`, think=false, temp 0, schema-constrained `format`, schema-in-prompt; long docs → `qwen3-30b-a3b-instruct-2507`) + a cassette/fake client for offline tests; `jsonschema` post-validation of every response
- [ ] 2.3 `extract.py`: two-stage per-chunk extraction (entities typed to ontology `entity_types`, then relations constrained to `relation_types`) + merge/dedupe across chunks into a typed node-link graph with `source_file`/`source_location` provenance; flat (non-recursive) schemas
- [ ] 2.4 `cluster.py`: deterministic networkx greedy-modularity community assignment (integer `community` ids); add `networkx` dependency
- [ ] 2.5 `backends/llm_backend.py`: `LlmBackend(client=...)` implementing `GraphBackend.generate`; assembles chunk → two-stage extract → merge → cluster → validate (node-link + `graph_validate` with types enforced); register `"llm"` in `generate.BACKENDS`
- [ ] 2.6 URL acquisition in `acquire.py`: classify `"url"`; fetch via `llm-wiki/scripts/scrape.py` → clean markdown into `raw/`; untrusted-content sanitization + provenance (`fetched_at`, `is_verbatim`); offline stub test, live behind a `network` marker
- [ ] 2.7 End-to-end (offline, cassette): fixture source + ontology → `llm` backend → typed `graph.json` → compile pipeline → `llm-wiki lint` 0 findings

## 3. G3 — Claude-native extraction path + eval harness

(The Anthropic SDK adapter and cross-provider API-parity test are DROPPED: this is a
Claude skill suite run inside Claude Code, so Claude itself is the extractor — no SDK, no
API key. The Ollama adapter remains the headless/standalone fallback.)

- [ ] 3.1 `prep.py`: stage the source, chunk it with the same `chunk_text` the backend uses, and emit a `worksheet.json` (per chunk: text + entity/relation prompts + allowed ontology types) so Claude's per-chunk extraction aligns with the backend's chunking; unit-tested
- [ ] 3.2 `generate.py --cassette <file>`: run the `llm` backend from a recorded responses file (`LlmBackend(CassetteClient(json.load(file)))`), so Claude's worksheet answers assemble into a typed graph via the existing merge/dedupe/cluster/validate pipeline; CLI-level test
- [ ] 3.3 SKILL.md Claude-native procedure: read the worksheet, perform two-stage extraction per chunk (entities typed to ontology, then relations constrained to it), write `responses.json` in backend order, then `generate --cassette` → handoff to compile. No Ollama/keys required
- [ ] 3.4 `evaluate.py`: `score(predicted_graph, gold_graph) -> {entities:{precision,recall,f1}, relations:{precision,recall,f1}}` (entities matched by normalized `(name,type)`, relations by normalized typed triple); unit-tested on crafted predicted-vs-gold pairs
- [ ] 3.5 Gold fixture (synthetic labeled source + gold graph) + an offline eval harness: run a backend via cassette over the gold source → predicted graph → `score` vs gold → report; live model comparison/tuning is a marker-gated/manual runbook, not committed test code
