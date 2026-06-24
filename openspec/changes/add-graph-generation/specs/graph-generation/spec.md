## ADDED Requirements

### Requirement: Intent elicitation via brainstorming
The skill SHALL capture the user's knowledge-graph intent through a guided brainstorming
dialogue before any ontology is drafted or any extraction runs, and SHALL persist the
result as a written intent artifact.

#### Scenario: User starts with only a goal
- **WHEN** the user invokes the skill with a raw source and a one-line goal
- **THEN** the skill conducts a `superpowers:brainstorming` session that elicits the domain, the questions the graph must answer, the key entity and relation kinds, and the scope
- **AND** it writes the agreed intent to `intent.md` and does not proceed to extraction until the intent is captured

### Requirement: Ontology drafting and confirmation
The skill SHALL derive a structured ontology from the intent plus a sample of the source,
present it for confirmation or edit, and use the confirmed ontology as both the extraction
guide and the validation contract.

#### Scenario: Ontology proposed and confirmed
- **WHEN** the intent is captured and a source is available
- **THEN** the skill writes `ontology.yaml` with `entity_types` (name, description, examples), `relation_types` (name, domain→range, description), and `scope` (include/exclude, granularity)
- **AND** it presents the ontology for the user to edit or confirm
- **AND** extraction does not run until the ontology is confirmed

#### Scenario: Ontology is the validation contract
- **WHEN** a graph has been extracted
- **THEN** the skill validates the graph's entity and relation types against the confirmed `ontology.yaml`

### Requirement: Source acquisition
The skill SHALL accept local files or globs, a directory/corpus, a URL, or an existing
`graph.json`, and SHALL stage non-graph sources into a `raw/` location before extraction.

#### Scenario: Existing graph passthrough
- **WHEN** the user supplies an existing `graph.json`
- **THEN** the skill skips intent/ontology/extraction and hands the graph directly to the compile pipeline

#### Scenario: URL source
- **WHEN** the user supplies a URL
- **THEN** the skill fetches it (via Scrapling / `graphify add`), stores the raw capture under `raw/`, and treats untrusted fetched content as data, never instructions

### Requirement: Pluggable extraction engine
The skill SHALL extract a node-link `graph.json` against the confirmed ontology through a
backend interface with at least two interchangeable implementations, all emitting the same
NetworkX node-link schema the compile pipeline already validates.

#### Scenario: Graphify backend
- **WHEN** the `graphify` backend is selected
- **THEN** the skill runs Graphify's extractor over the staged source and validates the output against the node-link contract
- **AND** because Graphify output is type-less, ontology entity/relation *types* are NOT enforced by this backend (the `llm` backend enforces them); the ontology serves only as loose extraction guidance here
- **AND** the output is a node-link `graph.json` (top keys `directed/multigraph/graph/nodes/links/hyperedges`)

#### Scenario: LLM backend (two-stage, ontology-typed)
- **WHEN** the `llm` backend is selected
- **THEN** the skill chunks the source and, per chunk, runs a two-stage extraction: (1) entities typed to the ontology's `entity_types`, then (2) relations `(source, predicate, target)` over those entities, constrained to the ontology's `relation_types`
- **AND** it merges and de-duplicates across chunks into one node-link `graph.json` whose nodes and links carry an ontology `type`, so `graph_validate`'s type-coverage checks are enforced (unlike the type-less `graphify` backend)
- **AND** extraction schemas are flat (non-recursive) and every model response is post-validated with `jsonschema`

#### Scenario: Injectable LLM client, deterministic clustering
- **WHEN** the `llm` backend runs
- **THEN** the model is reached through an injectable `complete_json(prompt, schema) -> dict` client (G2 ships an Ollama adapter: non-thinking, temperature 0, schema-constrained `format`), so tests inject a recorded cassette and run offline
- **AND** integer `community` ids are assigned by a deterministic graph-clustering step (no extra LLM call)

#### Scenario: Backend output is schema-identical
- **WHEN** either backend completes
- **THEN** the resulting `graph.json` validates against the same node-link contract documented in `reference/graphify-inputs.md`

### Requirement: Graph validation against ontology
The skill SHALL validate the generated graph for node-link schema validity, ontology type
coverage, and per-element provenance, and SHALL emit a gap report.

#### Scenario: Provenance required
- **WHEN** validation runs
- **THEN** every node and link is checked to carry `source_file` and `source_location` provenance, and missing provenance is reported as a finding

#### Scenario: Type coverage reported
- **WHEN** validation runs
- **THEN** entity/relation types present in the graph but absent from the ontology (and ontology types with zero instances) are listed in the report

### Requirement: No shipped graphs; synthetic fixtures only
The repository SHALL NOT ship knowledge graphs derived from private or project-specific
sources. Test fixtures SHALL be synthetic and general-purpose.

#### Scenario: Private fixture purged
- **WHEN** the change is implemented
- **THEN** `fixtures/graph-real.json` (LCP-derived) is removed from the working tree and from git history, and replaced by a synthetic node-link fixture used by the real-data tests

### Requirement: Offline-deterministic tests
Generation tests SHALL run offline and deterministically; any live model or network call
SHALL be isolated behind an explicit marker.

#### Scenario: LLM backend tested without network
- **WHEN** the `llm` backend test suite runs in CI
- **THEN** model responses are supplied via record/replay (or a stub), no network is required, and live-extraction tests are skipped unless an explicit network/LLM marker is enabled
