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

- [ ] 2.1 Implement the `llm` backend: chunk → strict-JSON node-link extraction constrained by the ontology → merge/dedupe/cluster (record/replay tests; offline)
- [ ] 2.2 Wire the model-selection defaults (local Ollama + Claude API) from the research report, including non-thinking/strict-JSON settings
- [ ] 2.3 Implement URL acquisition (Scrapling / `graphify add`) with untrusted-content sanitization (tests; network marker-gated)
- [ ] 2.4 Backend-parity test: same fixture source + ontology through both backends yields schema-identical, ontology-valid graphs

## 3. G3 — Model tuning and extraction evals

- [ ] 3.1 Extraction-quality eval harness (precision/recall of entities + typed relations vs. a labeled synthetic fixture)
- [ ] 3.2 Per-backend/model comparison run + recorded metrics; tune quant/context/temperature for the local default
- [ ] 3.3 Publish-readiness check: confirm no private data in tree or history, then the repo is safe to push
