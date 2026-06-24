## Why

The suite today starts from an existing Graphify `graph.json` and compiles it into an
`llm-wiki`-format wiki. It gives users no way to *build* that graph from their own raw
information source — and Graphify's own extraction is generic, not steered by the
knowledge graph the user actually wants. This change adds the missing front door:
request-driven graph generation, so the product is **tooling to build a project's
knowledge graph and make it LLM-accessible**, not a shipped graph.

## What Changes

A new dedicated skill, `generating-knowledge-graph`, that turns a raw source plus a
brainstormed intent into a `graph.json` the existing `compiling-graphify-wiki` pipeline
consumes. It:

- conducts a `superpowers:brainstorming` dialogue to capture the user's *graph intent*;
- drafts a structured `ontology.yaml` (entity/relation types + scope) from that intent and
  a sample of the source, and has the user confirm/edit it;
- acquires the raw source (local files/globs, a directory/corpus, a URL, or an existing
  `graph.json` passthrough);
- extracts a node-link `graph.json` against the ontology via a **pluggable engine** with
  two backends — `graphify` (wraps Graphify's extractor, steered by the ontology) and
  `llm` (request-guided strict-JSON extraction);
- validates the graph against the ontology (type coverage, schema, provenance) and reports
  gaps; then hands `graph.json` to `compiling-graphify-wiki`.

It also reframes test data: **graphs are user-generated, never shipped.** The repo ships
only synthetic, general-purpose fixtures. The LCP-derived `fixtures/graph-real.json` is
purged from the working tree and git history and replaced with a synthetic node-link
fixture, making the repo safe to publish.

## Capabilities

### New Capabilities
- `graph-generation`: brainstorm intent → ontology → acquire source → pluggable extraction → node-link `graph.json` → validate vs ontology → handoff to the compile pipeline.

### Modified Capabilities
- None. The compile pipeline (`graph.json` → wiki) is unchanged; generation produces the same node-link schema it already consumes.

## Impact

- New skill `skills/generating-knowledge-graph/` (SKILL.md, scripts, schemas, fixtures, tests) in the existing plugin.
- New dependency surface: the `graphify` backend shells out to the installed `graphify`/`graphifyy` CLI (local Ollama); the `llm` backend calls a configured model (local Ollama default + Claude API default, chosen by the model-selection research).
- Test data change: remove `fixtures/graph-real.json` (LCP-derived) from tree and history; add synthetic node-link + ontology fixtures. Unblocks publishing the repo.
- No change to `compiling-graphify-wiki` behavior or to the bundled `llm-wiki` skill.
