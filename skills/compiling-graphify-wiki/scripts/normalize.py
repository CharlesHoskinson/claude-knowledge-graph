#!/usr/bin/env python3
"""Real Graphify node-link graph.json -> canonical snapshot.
Graphify has no semantic node types, no descriptions, no documents/communities
arrays: every node -> concept; sources/communities are derived. See
reference/graphify-inputs.md."""
import argparse, json, re, sys

_STRIP_EXT = re.compile(r"\.(md|json|py|txt|html?|pdf)$", re.I)
_UNSAFE = re.compile(r'[/\\:*?"<>|]')

def _source_title(source_file):
    return _UNSAFE.sub("-", _STRIP_EXT.sub("", source_file))

def _nodes(raw_nodes):
    out = []
    for n in raw_nodes:
        ft = n.get("file_type")
        out.append({
            "id": str(n["id"]),
            "kind": "concept",
            "title": n.get("label") or n.get("norm_label") or str(n["id"]),
            "aliases": [],
            "description": "",
            "tags": [ft] if ft else [],
            "entity_kind": None,
            "source_ids": [n["source_file"]] if n.get("source_file") else [],
            "source_location": n.get("source_location") or "",
        })
    return out

def _edges(raw_links):
    out = []
    for i, l in enumerate(raw_links, start=1):
        out.append({
            "id": f"e{i}",
            "source": str(l["source"]),
            "target": str(l["target"]),
            "predicate": l.get("relation") or "related-to",
            "source_ids": [l["source_file"]] if l.get("source_file") else [],
            "source_location": l.get("source_location") or "",
        })
    return out

def _sources(raw_nodes):
    seen = {}
    for n in raw_nodes:
        sf = n.get("source_file")
        if sf and sf not in seen:
            seen[sf] = {"source_id": sf, "title": _source_title(sf), "uri": n.get("source_url") or ""}
    return list(seen.values())

def _communities(raw_nodes):
    groups = {}
    for n in raw_nodes:
        c = n.get("community")
        if c is None:
            continue
        groups.setdefault(int(c), []).append(str(n["id"]))
    out = []
    for c in sorted(groups):
        out.append({"id": f"c{c}", "title": f"Community {c}", "summary": "",
                    "member_node_ids": groups[c]})
    return out

def normalize(raw, snapshot_id, created_at):
    nodes = raw.get("nodes", [])
    links = raw.get("links") or raw.get("edges") or []
    return {
        "snapshot_id": snapshot_id,
        "created_at": created_at,
        "nodes": _nodes(nodes),
        "edges": _edges(links),
        "sources": _sources(nodes),
        "communities": _communities(nodes),
    }

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--snapshot-id", default="snapshot")
    ap.add_argument("--created-at", default="2026-06-24T00:00:00Z")
    a = ap.parse_args(argv)
    raw = json.loads(open(a.graph, encoding="utf-8").read())
    snap = normalize(raw, a.snapshot_id, a.created_at)
    open(a.out, "w", encoding="utf-8").write(json.dumps(snap, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
