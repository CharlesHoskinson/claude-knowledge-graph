#!/usr/bin/env python3
"""Orchestrate generation: backend -> graph.json -> validate vs ontology -> report."""
import sys, pathlib
_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "backends"):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import argparse, json, yaml, subprocess
import graph_validate
from graphify_backend import GraphifyBackend
from llm_backend import LlmBackend
from llm_client import make_ollama_client, CassetteClient

BACKENDS = {
    "graphify": lambda: GraphifyBackend(),
    "llm": lambda: LlmBackend(make_ollama_client()),
}

def generate_graph(manifest, ontology_obj, backend, out_path, report_path, run=subprocess.run):
    graph = backend.generate(manifest, ontology_obj, out_path, run=run)
    report = graph_validate.validate_graph(graph, ontology_obj)
    # surface relations the backend dropped during extraction (fix A1); informational, never fails
    drops = getattr(backend, "relation_drops", None)
    if drops is not None:
        report["relation_drops"] = drops
        if drops.get("total", 0) > 0:
            report.setdefault("findings", []).append({
                "severity": "warning", "category": "relation-drops",
                "message": f"{drops['total']} relation(s) dropped during extraction: {drops['by_reason']}",
                "path": "extraction"})
            if report["result"] == "pass":
                report["result"] = "warn"
    pathlib.Path(report_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["result"] == "fail":
        raise RuntimeError(f"generated graph failed validation: {report['findings'][:5]}")
    return {"graph": graph, "report": report}

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--backend", choices=sorted(BACKENDS), default="graphify")
    ap.add_argument("--cassette", default=None)
    ap.add_argument("--chunk-size", type=int, default=1200)
    ap.add_argument("--overlap", type=int, default=150)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args(argv)
    if not (0 <= a.overlap < a.chunk_size):
        ap.error(f"--overlap must satisfy 0 <= overlap < chunk-size, got overlap={a.overlap}, chunk-size={a.chunk_size}")
    manifest = json.loads(pathlib.Path(a.manifest).read_text(encoding="utf-8"))
    ont = yaml.safe_load(pathlib.Path(a.ontology).read_text(encoding="utf-8"))
    if a.cassette:
        responses = json.loads(pathlib.Path(a.cassette).read_text(encoding="utf-8"))
        backend = LlmBackend(CassetteClient(responses), chunk_size=a.chunk_size, overlap=a.overlap)
    else:
        backend = BACKENDS[a.backend]()
    res = generate_graph(manifest, ont, backend, a.out, a.report)
    print(json.dumps(res["report"], indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
