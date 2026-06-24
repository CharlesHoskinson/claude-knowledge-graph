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
- **Model selection (from the citation-backed research, 2026-06-24).** Defaults wired into
  the `llm` backend:
  - **Local default:** `qwen2.5-32b-instruct` Q4_K_M on Ollama (the box's
    `qwen2.5-32b-graphrag` tag is this base + a GraphRAG prompt — verify with
    `ollama show --modelfile`). Run **non-thinking**, `temperature 0`, with a JSON-schema
    `format` and the schema also pasted into the prompt. For sources > ~32K tokens, switch
    to `qwen3-30b-a3b-instruct-2507` (262K context, emits no `<think>` by design). Cap
    context on the 32 GB card (Q4 at long context can exceed 32 GB VRAM).
  - **API default:** Claude **Haiku 4.5** for high-volume extraction (Sonnet 4.6 for hard
    sources / entity resolution), via native **Structured Outputs / strict tool use**, with
    **extended thinking OFF**, `temperature 0`, and a **flattened (non-recursive)** graph
    schema.
  - **Cross-cutting rules (both modes):** thinking/reasoning mode breaks strict JSON —
    always run non-thinking. Constrained decoding guarantees JSON *shape, not correctness*,
    so the graph-vs-ontology validator (and triple-level checks) is mandatory regardless of
    model. Favor **scaffolded/two-stage extraction** (KGGen-style) over picking a bigger
    model — scaffolding closes most of the quality gap. Full report:
    `scratchpad/best-llm-kg-extraction.md` (kept out of the repo).
- **Fixtures are synthetic.** Because graphs are user-generated, the repo ships only
  synthetic node-link + ontology fixtures. `fixtures/graph-real.json` is purged from tree
  and history.
- **Claude-native extraction (no API key).** This is a Claude skill suite run in Claude
  Code, so Claude itself is the extractor — the **Anthropic SDK adapter and API-provider
  parity test are dropped**. Claude performs the two-stage extraction (guided by SKILL.md +
  a `prep` worksheet) and its answers assemble through the existing `llm` backend via
  `generate --cassette`. The Ollama adapter remains the headless/standalone fallback; the
  API-default model notes above are reference only.
- **Staging.** G1 = scaffold + intent-brainstorm + ontology draft/confirm + backend
  interface + `graphify` backend + acquire(files/dir) + validate + handoff + fixture purge.
  G2 = `llm` backend (Ollama) + URL acquisition. G3 = Claude-native extraction path
  (`prep` + `generate --cassette` + SKILL.md) + extraction-quality eval harness.

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
