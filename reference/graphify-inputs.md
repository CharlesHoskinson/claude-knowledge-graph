# Graphify Inputs (real schema)

Ground truth: `fixtures/graph-real.json` (a real Graphify export). `graph.json` is a
NetworkX node-link dict.

## Top-level keys
`directed`, `multigraph`, `graph`, `nodes`, `links` (NOT "edges"), `hyperedges`.

## Node fields → canonical
| canonical | real field | notes |
|---|---|---|
| id | `id` | stable |
| kind | — | always `concept` (no semantic type in graphify output) |
| title | `label` | display name; `norm_label` is the normalized form |
| description | — | absent; pages have no Definition text from the graph |
| tags | `file_type` | single-value tag (e.g. `doc`, `code`) |
| source_ids | `source_file` | provenance file path |
| source_location | `source_location` | line locator e.g. `L10` |
| community | `community` | INTEGER cluster id (node attribute) |

## Link fields → canonical edge
| canonical | real field |
|---|---|
| source / target | `source` / `target` |
| predicate | `relation` |
| source_ids | `source_file` |
| source_location | `source_location` |

## Derived (not arrays in graph.json)
- **sources:** distinct `source_file` across nodes+links; `uri` from the node's `source_url`; `title` = sanitized `source_file` with the extension stripped.
- **communities:** group node ids by the integer `community`; `title` = `Community <n>` (real names live in `GRAPH_REPORT.md`, not consumed in Stage 1).
