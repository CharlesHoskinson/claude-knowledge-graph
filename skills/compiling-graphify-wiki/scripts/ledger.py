#!/usr/bin/env python3
"""Canonical snapshot -> claim ledger. Claims come from relations (edges) and
communities; graphify nodes carry no descriptions, so there are no attribute claims."""
import argparse, json, sys, yaml

def _titles(snapshot):
    return {n["id"]: n["title"] for n in snapshot["nodes"]}

def build_ledger(snapshot, ledger_id):
    titles = _titles(snapshot)
    claims, n = [], 0
    def add(**kw):
        nonlocal n
        n += 1
        base = {"claim_id": f"CLM-{n:04d}", "node_id": kw.pop("node_id", None),
                "graphify_nodes": kw.pop("graphify_nodes", []),
                "graphify_edges": kw.pop("graphify_edges", []),
                "source_ids": kw.pop("source_ids", []), "contradicts": []}
        base.update(kw)
        claims.append(base)
    for e in snapshot["edges"]:
        srcs = e.get("source_ids", [])
        text = f"{titles.get(e['source'], e['source'])} {e['predicate']} {titles.get(e['target'], e['target'])}."
        add(text=text, claim_type="edge", status="supported" if srcs else "inferred",
            node_id=e["source"], graphify_nodes=[e["source"], e["target"]],
            graphify_edges=[e["id"]], source_ids=srcs, source_location=e.get("source_location", ""))
    for comm in snapshot["communities"]:
        members = [titles.get(m, m) for m in comm.get("member_node_ids", [])]
        text = f"{comm['title']} groups: {', '.join(members)}."
        add(text=text, claim_type="community_summary", status="inferred",
            node_id=None, graphify_nodes=list(comm.get("member_node_ids", [])))
    return {"ledger_id": ledger_id, "graph_snapshot_id": snapshot["snapshot_id"],
            "created_at": snapshot["created_at"], "claims": claims}

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ledger-id", default="ledger")
    a = ap.parse_args(argv)
    snap = json.loads(open(a.snapshot, encoding="utf-8").read())
    led = build_ledger(snap, a.ledger_id)
    open(a.out, "w", encoding="utf-8").write(yaml.safe_dump(led, sort_keys=False, allow_unicode=True))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
