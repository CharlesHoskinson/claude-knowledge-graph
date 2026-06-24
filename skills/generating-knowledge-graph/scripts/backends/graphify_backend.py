#!/usr/bin/env python3
"""Thin graphify-CLI backend. Graphify output is type-less, so ontology types are
NOT enforced here (the llm backend does that). The CLI call is injectable for tests."""
import json, sys, pathlib, subprocess
from base import GraphBackend
import node_link

class GraphifyBackend(GraphBackend):
    name = "graphify"

    def generate(self, manifest, ontology, out_path, run=subprocess.run):
        raw_dir = pathlib.Path(manifest["raw_dir"])
        # Live invocation (faked in tests). Ontology is passed as loose guidance only.
        proc = run([sys.executable, "-m", "graphify", "extract", str(raw_dir),
                    "--backend", "ollama", "--out", str(raw_dir / "graphify-out")],
                   capture_output=True, text=True)
        graph_path = raw_dir / "graphify-out" / "graph.json"
        if getattr(proc, "returncode", 1) != 0 or not graph_path.exists():
            raise RuntimeError(f"graphify produced no graph at {graph_path}; "
                               f"stderr={getattr(proc, 'stderr', '')[:500]}")
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        findings = node_link.validate_node_link(graph)
        if findings:
            raise RuntimeError(f"graphify output failed node-link validation: {findings[:3]}")
        pathlib.Path(out_path).write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        return graph
