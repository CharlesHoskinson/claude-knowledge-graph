#!/usr/bin/env python3
"""LLM extraction backend: chunk -> two-stage extract -> merge -> cluster -> typed node-link."""
import json, pathlib, subprocess
from base import GraphBackend
import extract, cluster, node_link
import chunk as chunker
from llm_client import CassetteClient

class LlmBackend(GraphBackend):
    name = "llm"

    def __init__(self, client, chunk_size=1200, overlap=150):
        self.client = client
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _total_chunks(self, manifest):
        raw_dir = pathlib.Path(manifest["raw_dir"])
        total = 0
        for f in manifest["files"]:
            text = (raw_dir / f["path"]).read_text(encoding="utf-8")
            total += len(chunker.chunk_text(text, self.chunk_size, self.overlap))
        return total

    def generate(self, manifest, ontology, out_path, run=subprocess.run):
        # Each chunk drives exactly two cassette calls (entities, then relations); a
        # mismatched recording silently truncates or ignores extras, so fail loudly (fix A4).
        if isinstance(self.client, CassetteClient):
            expected = 2 * self._total_chunks(manifest)
            actual = len(self.client._responses)
            if actual != expected:
                raise ValueError(
                    f"cassette length mismatch: expected {expected} responses "
                    f"(2 x {expected // 2} chunks) but got {actual} "
                    f"(chunk_size={self.chunk_size}, overlap={self.overlap})")
        nodes, links = {}, {}
        drops = {"unknown_predicate": 0, "unresolved_source": 0, "unresolved_target": 0}
        drop_samples = []
        raw_dir = pathlib.Path(manifest["raw_dir"])
        for f in manifest["files"]:
            text = (raw_dir / f["path"]).read_text(encoding="utf-8")
            g = extract.extract_graph(text, ontology, self.client, source_file=f["path"],
                                      chunk_size=self.chunk_size, overlap=self.overlap)
            for n in g["nodes"]:
                nodes.setdefault(n["id"], n)
            for l in g["links"]:
                links.setdefault((l["source"], l["relation"], l["target"]), l)
            rd = g.get("relation_drops", {})
            for reason, count in rd.get("by_reason", {}).items():
                drops[reason] = drops.get(reason, 0) + count
            for s in rd.get("sample", []):
                if len(drop_samples) < 5:
                    drop_samples.append(s)
        # surfaced for generate_graph -> report.json; see fix A1
        self.relation_drops = {"total": sum(drops.values()), "by_reason": drops,
                               "sample": drop_samples}
        graph = {"directed": True, "multigraph": False, "graph": {},
                 "nodes": list(nodes.values()), "links": list(links.values()), "hyperedges": []}
        cluster.assign_communities(graph)
        findings = node_link.validate_node_link(graph)
        if findings:
            raise RuntimeError(f"llm backend produced invalid node-link graph: {findings[:3]}")
        pathlib.Path(out_path).write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        return graph
