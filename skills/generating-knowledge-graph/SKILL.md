---
name: generating-knowledge-graph
description: Build a knowledge graph (graph.json) from a raw source, steered by a brainstormed intent and a confirmed ontology, then hand it to compiling-graphify-wiki. Use when the user wants to construct a knowledge graph for a project from their own files/corpus and make it accessible to the wiki.
allowed-tools: Read Grep Glob Bash(python *) Bash(python3 *)
---

# Generating Knowledge Graph (G1)

Pipeline: brainstorm intent -> ontology.yaml -> acquire source -> extract (graphify backend) -> validate vs ontology -> hand graph.json to compiling-graphify-wiki.

1. Capture intent via `superpowers:brainstorming`; write `intent.md`.
2. Draft `ontology.yaml` from intent + a sample of the source; confirm with the user.
3. `python scripts/acquire.py --inputs <files-or-dir> --raw <raw/> --out <manifest.json>`
4. `python scripts/generate.py --manifest <manifest.json> --ontology <ontology.yaml> --backend graphify --out <graph.json> --report <report.json>`
5. Hand `<graph.json>` to compiling-graphify-wiki (normalize -> ledger -> compile).
