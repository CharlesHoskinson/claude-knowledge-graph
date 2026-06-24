#!/usr/bin/env python3
"""Validate a graph dict against the NetworkX node-link contract."""
import json, pathlib, jsonschema

_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "graphify-node-link.schema.json"

def validate_node_link(graph):
    findings = []
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(graph, schema)
    except jsonschema.ValidationError as e:
        return [{"severity": "error", "category": "node-link-schema",
                 "message": str(e.message), "path": "/".join(str(p) for p in e.absolute_path)}]
    ids = {n["id"] for n in graph["nodes"]}
    for i, link in enumerate(graph["links"]):
        for endpoint in ("source", "target"):
            if link.get(endpoint) not in ids:
                findings.append({"severity": "error", "category": "dangling-endpoint",
                                 "message": f"link[{i}] {endpoint} '{link.get(endpoint)}' not a node id",
                                 "path": f"links/{i}/{endpoint}"})
    return findings
