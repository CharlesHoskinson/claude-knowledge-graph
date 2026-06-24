#!/usr/bin/env python3
"""Validate a generated graph against the node-link contract and the ontology."""
import argparse, json, sys, pathlib, yaml
import node_link

def validate_graph(graph, ontology):
    findings = list(node_link.validate_node_link(graph))   # node-link errors first
    # empty graph (warn) — a blank source yields no nodes; flag it rather than silently pass
    if not graph.get("nodes"):
        findings.append({"severity": "warning", "category": "empty-graph",
                         "message": "graph has no nodes (empty/blank source?)", "path": "nodes"})
    # provenance (warn)
    for i, n in enumerate(graph.get("nodes", [])):
        if not n.get("source_file") or not n.get("source_location"):
            findings.append({"severity": "warning", "category": "missing-provenance",
                             "message": f"node '{n.get('id')}' lacks source_file/source_location",
                             "path": f"nodes/{i}"})
    # type coverage (only when the graph carries types)
    entity_names = {e["name"] for e in ontology.get("entity_types", [])}
    relation_names = {r["name"] for r in ontology.get("relation_types", [])}
    typed_nodes = [n for n in graph.get("nodes", []) if n.get("type")]
    if typed_nodes:
        for n in typed_nodes:
            if n["type"] not in entity_names:
                findings.append({"severity": "error", "category": "unknown-type",
                                 "message": f"node '{n.get('id')}' type '{n['type']}' not in ontology entity_types",
                                 "path": f"node/{n.get('id')}"})
        present = {n["type"] for n in typed_nodes}
        for missing in sorted(entity_names - present):
            findings.append({"severity": "warning", "category": "unused-entity-type",
                             "message": f"ontology entity_type '{missing}' has no instances", "path": "ontology"})
    typed_links = [link for link in graph.get("links", []) if link.get("type")]
    for link in typed_links:
        if link["type"] not in relation_names:
            findings.append({"severity": "error", "category": "unknown-type",
                             "message": f"link type '{link['type']}' not in ontology relation_types",
                             "path": "links"})
    # domain/range conformance (warn) — declared relation endpoints must match node types
    node_type = {n.get("id"): n.get("type") for n in graph.get("nodes", [])}
    rel_dr = {r["name"]: (r.get("domain"), r.get("range")) for r in ontology.get("relation_types", [])}
    for link in typed_links:
        if link["type"] not in rel_dr:
            continue
        domain, range_ = rel_dr[link["type"]]
        s_type, t_type = node_type.get(link.get("source")), node_type.get(link.get("target"))
        if (s_type is not None and domain is not None and s_type != domain) or \
           (t_type is not None and range_ is not None and t_type != range_):
            findings.append({"severity": "warning", "category": "relation-domain-range",
                             "message": (f"link '{link['type']}' expects {domain}->{range_} but "
                                         f"connects {s_type}->{t_type}"),
                             "path": "links"})
    sev = {f["severity"] for f in findings}
    result = "fail" if "error" in sev else ("warn" if "warning" in sev else "pass")
    return {"result": result, "findings": findings}

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True)
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    graph = json.loads(pathlib.Path(a.graph).read_text(encoding="utf-8"))
    ont = yaml.safe_load(pathlib.Path(a.ontology).read_text(encoding="utf-8"))
    rep = validate_graph(graph, ont)
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return 0 if rep["result"] != "fail" else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
