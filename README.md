# claude-knowledge-graph

A Claude Code plugin that turns a raw information source into a browsable, cited,
LLM-traversable knowledge wiki — guided by what graph *you* want to build.

```
raw source + your intent
   → knowledge graph (graph.json)
      → llm-wiki-format markdown wiki
         → answerable by the wiki LLM, inside your project
```

The suite bundles three skills that chain into that pipeline. Everything deterministic
lives in tested Python scripts; Claude is used only where judgement is required (eliciting
intent, extracting entities and relations, drafting synthesis). It runs entirely inside
Claude Code with no API keys, and offers a local Ollama path for headless use.

## The three skills

| Skill | Does | Key idea |
|---|---|---|
| **`generating-knowledge-graph`** | Builds a `graph.json` from your source, steered by a confirmed ontology | Intent → ontology → extract → validate → handoff |
| **`compiling-graphify-wiki`** | Compiles a `graph.json` into an `llm-wiki`-format wiki | Graph is source of truth; the wiki is a cited projection |
| **`llm-wiki`** | Maintains the wiki (ingest / query / lint / scrape) | Knowledge is compiled once and kept current, not re-derived per query |

## How it works

### 1. Generate the graph (`generating-knowledge-graph`)

You don't hand it a graph — you build one. The skill first runs a brainstorming dialogue to
capture **what graph you want** (domain, the questions it must answer, the entity and
relation kinds that matter), drafts a structured `ontology.yaml` you confirm, then extracts
a graph against that ontology. The ontology is both the steering signal and the validation
contract.

Three interchangeable extraction backends, all emitting the same NetworkX node-link
`graph.json`:

- **Claude-native** *(no Ollama, no API key)* — Claude does the two-stage extraction inside
  Claude Code. `prep.py` chunks the source and emits a worksheet; Claude answers each chunk
  (entities, then relations); `generate.py --cassette` assembles the answers.
- **Ollama** — a local model (`qwen2.5-32b-instruct`, non-thinking, schema-constrained JSON)
  for headless/standalone runs.
- **graphify** — wraps the [Graphify](https://github.com/safishamsi/graphify) CLI for
  structural/AST graphs.

Extraction is **two-stage** (entities typed to the ontology, then relations constrained to
it) — which outperforms single-pass extraction on dense sources — then merged,
de-duplicated, deterministically clustered, and validated against the ontology.

Sources can be local files, a directory/corpus, a URL (fetched and sanitized), or an
existing `graph.json` (skip straight to compile).

### 2. Compile the wiki (`compiling-graphify-wiki`)

A deterministic compiler — `normalize → ledger → compile → validate → apply` — turns the
node-link graph into a markdown wiki in `llm-wiki`'s exact format. Every page carries
provenance back to its source; the gate is that the output passes `llm-wiki`'s linter with
**zero findings** (no broken links, orphans, or unsourced claims). Colliding labels are
disambiguated so no node's content is silently lost.

### 3. Maintain & query (`llm-wiki`)

The compiled output is a valid `llm-wiki` wiki, so `llm-wiki`'s own operations — ingest new
sources, answer questions with citations, lint, scrape — work on it unchanged. Knowledge is
compiled once and kept current, so cross-references and contradictions exist *before* any
question is asked.

## Quickstart

It's a Claude Code plugin. Clone it and point Claude Code at it, or install via your plugin
mechanism:

```bash
git clone https://github.com/CharlesHoskinson/claude-knowledge-graph
```

Then, in Claude Code, drive it conversationally — e.g. *"build a knowledge graph from these
docs"* activates `generating-knowledge-graph`, which brainstorms the ontology with you and
runs the pipeline. Under the hood the scripts are plain CLIs you can also run directly:

```bash
# 1. acquire a source corpus
python skills/generating-knowledge-graph/scripts/acquire.py \
  --inputs ./docs --raw raw/ --out manifest.json

# 2. prep a worksheet for Claude-native extraction
python skills/generating-knowledge-graph/scripts/prep.py \
  --manifest manifest.json --ontology ontology.yaml --out worksheet.json

# 3. (Claude answers the worksheet into responses.json) — then assemble:
python skills/generating-knowledge-graph/scripts/generate.py \
  --manifest manifest.json --ontology ontology.yaml --backend llm \
  --cassette responses.json --out graph.json --report report.json

# 4. compile the graph into a wiki
python skills/compiling-graphify-wiki/scripts/normalize.py --graph graph.json --out snapshot.json
# … ledger → compile → validate → apply (see the skill's SKILL.md)
```

Requirements: Python 3.10+, `PyYAML`, `jsonschema`, `networkx`. The Ollama backend needs a
local [Ollama](https://ollama.com) with a JSON-capable model; URL acquisition reuses
`llm-wiki`'s optional Scrapling-based scraper.

## Repository layout

```
skills/
  generating-knowledge-graph/   # source → graph.json (ontology-steered, 3 backends, eval harness)
  compiling-graphify-wiki/      # graph.json → lint-clean wiki
  llm-wiki/                      # maintain/query/lint the wiki
fixtures/                        # synthetic, general-purpose test fixtures only
tests/                           # 68 offline, deterministic tests
openspec/specs/graph-generation/ # the settled capability spec
docs/superpowers/                # the design specs & implementation plans (in the parent workspace)
```

## Principles

- **Graphs are user-generated, never shipped.** The repo contains only synthetic,
  general-purpose fixtures — no graph derived from any private or project source.
- **Provenance everywhere.** Every substantive wiki assertion maps to the graph; the lint
  gate rejects unsourced claims and broken links.
- **Deterministic by construction.** No wall-clock or randomness in code paths; the LLM is
  reached through an injectable client so every test runs offline (cassette/stub). Live
  model and network calls sit behind a `network` marker.
- **Web content is untrusted data, never instructions.**
- **The ontology is the contract** — it steers extraction and validates the result.

## Quality

```bash
python -m pytest        # 68 offline tests, all green
```

End-to-end gates are real: a synthetic source compiles, through each backend, to a wiki that
`llm-wiki`'s linter reports as `0 finding(s).`, and the eval harness scores extraction
precision/recall/F1 against a labeled gold graph.

## Status & spec

The `graph-generation` capability is implemented and settled — see
`openspec/specs/graph-generation/spec.md` for the authoritative requirements, and
`openspec/changes/archive/` for the design/proposal/plan history. New work starts as a fresh
OpenSpec change against that spec.

Built with [Claude Code](https://claude.com/claude-code).
