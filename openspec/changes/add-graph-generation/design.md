## Context

`graphify-wiki-suite` is a Claude Code plugin bundling `llm-wiki` and
`compiling-graphify-wiki`. The compile pipeline (normalize → ledger → compile → validate →
apply) already turns a NetworkX node-link `graph.json` into an `llm-wiki`-format wiki that
passes `llm-wiki lint` with zero findings, verified on a real 74-node export. What is
missing is a way to *build* that graph from a user's raw source, steered by what graph the
user actually wants. Graphify can extract graphs locally (Ollama) but does so generically.

## Goals / Non-Goals

**Goals:**
- Request-driven generation: the user's intent (captured by brainstorming) steers extraction.
- A pluggable engine with `graphify` and `llm` backends, both emitting the same node-link schema.
- Accept files, a directory/corpus, a URL, or an existing graph.
- Validate the graph against the confirmed ontology; hand off to the compile pipeline.
- Ship only synthetic, general-purpose fixtures; purge the LCP-derived graph from tree + history.

**Non-Goals:**
- Re-implementing Graphify's chunking/clustering (the `graphify` backend reuses it).
- Changing the compile pipeline or `llm-wiki`.
- Shipping any specific knowledge graph.
- A production MCP server, Graphify writeback, or vector retrieval (covered by later stages).

## Decisions

- **Brainstorm as front door.** The skill runs a `superpowers:brainstorming` session to
  produce `intent.md` before drafting an ontology. Intent is elicited, not assumed.
- **Ontology is the contract.** `ontology.yaml` (entity_types, relation_types with
  domain→range, scope) is derived from intent + a source sample, user-confirmed, and used
  both to steer extraction and to validate the result. This makes a non-deterministic step
  auditable.
- **Pluggable backend interface.** `GraphBackend.generate(source, ontology, out_path) ->
  graph.json`. Two implementations: `graphify` (shell out to the installed CLI, inject the
  ontology as guidance, post-filter to ontology types) and `llm` (chunk → strict-JSON
  node-link extraction constrained by the ontology → merge/dedupe/cluster). Selection by
  flag/config. Both validate against the existing node-link contract.
- **Node-link is the seam.** Generation's only output contract to downstream is a valid
  node-link `graph.json`; everything in `compiling-graphify-wiki` stays unchanged.
- **Model selection from research.** A local Ollama default (RTX 5090 32 GB, with quant,
  context window, and a non-thinking/strict-JSON setting) and an API default (Claude) are
  chosen from a dedicated, citation-backed model-selection investigation, and wired into the
  two backends. (Investigation in flight; results fill this section's defaults.)
- **Fixtures are synthetic.** Because graphs are user-generated, the repo ships only
  synthetic node-link + ontology fixtures. `fixtures/graph-real.json` is purged from tree
  and history.
- **Staging.** G1 = scaffold + intent-brainstorm + ontology draft/confirm + backend
  interface + `graphify` backend + acquire(files/dir) + validate + handoff + fixture purge.
  G2 = `llm` backend + URL acquisition. G3 = model tuning + extraction-quality evals.

## Risks / Trade-offs

- **Extraction non-determinism.** LLM extraction varies run to run. Mitigated by the
  ontology contract + validation + record/replay tests; live extraction is marker-gated.
- **Backend skew.** Two backends can drift in output shape. Mitigated by a shared node-link
  validator both must pass and a shared fixture-source → graph contract test.
- **Local model fit/quality.** A 32 GB-fitting model may under-extract relations vs. a
  frontier API model. Mitigated by the model-selection research and by letting users pick
  the backend per run.
- **History rewrite.** Purging `graph-real.json` from history rewrites commits; acceptable
  because the repo has never been pushed. Verified absent before any publish.
- **Prompt injection from fetched/URL sources.** Treated as untrusted data, never
  instructions; sanitized before entering extraction prompts.
