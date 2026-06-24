#!/usr/bin/env python3
"""LLM extraction backend: chunk -> two-stage extract -> merge -> cluster -> typed node-link."""
import json, pathlib, subprocess
from base import GraphBackend
import extract, cluster, node_link

class LlmBackend(GraphBackend):
    name = "llm"

    def __init__(self, client, chunk_size=1200, overlap=150):
        self.client = client
        self.chunk_size = chunk_size
        self.overlap = overlap

    def generate(self, manifest, ontology, out_path, run=subprocess.run):
        nodes, links = {}, {}
        raw_dir = pathlib.Path(manifest["raw_dir"])
        for f in manifest["files"]:
            text = (raw_dir / f["path"]).read_text(encoding="utf-8")
            g = extract.extract_graph(text, ontology, self.client, source_file=f["path"],
                                      chunk_size=self.chunk_size, overlap=self.overlap)
            for n in g["nodes"]:
                nodes.setdefault(n["id"], n)
            for l in g["links"]:
                links.setdefault((l["source"], l["relation"], l["target"]), l)
        graph = {"directed": True, "multigraph": False, "graph": {},
                 "nodes": list(nodes.values()), "links": list(links.values()), "hyperedges": []}
        cluster.assign_communities(graph)
        findings = node_link.validate_node_link(graph)
        if findings:
            raise RuntimeError(f"llm backend produced invalid node-link graph: {findings[:3]}")
        pathlib.Path(out_path).write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        return graph
