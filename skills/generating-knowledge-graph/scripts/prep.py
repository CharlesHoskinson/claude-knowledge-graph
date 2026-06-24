#!/usr/bin/env python3
"""Build a per-chunk worksheet so Claude's two-stage extraction aligns with the llm
backend's chunking. The worksheet order MUST match LlmBackend.generate's chunk order."""
import sys, pathlib
_HERE = pathlib.Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "backends"):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import argparse, json, yaml
import chunk as chunker
import extract

def build_worksheet(manifest, ontology, chunk_size=1200, overlap=150):
    entity_types = [e["name"] for e in ontology.get("entity_types", [])]
    relation_types = [r["name"] for r in ontology.get("relation_types", [])]
    raw_dir = pathlib.Path(manifest["raw_dir"])
    worksheet = []
    for f in manifest["files"]:
        text = (raw_dir / f["path"]).read_text(encoding="utf-8")
        for i, ch in enumerate(chunker.chunk_text(text, chunk_size, overlap)):
            worksheet.append({
                "file": f["path"], "chunk_index": i, "text": ch,
                "entity_types": entity_types, "relation_types": relation_types,
                "entity_prompt": extract.entity_prompt(ch, ontology),
            })
    return worksheet

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--chunk-size", type=int, default=1200)
    ap.add_argument("--overlap", type=int, default=150)
    a = ap.parse_args(argv)
    if not (0 <= a.overlap < a.chunk_size):
        ap.error(f"--overlap must satisfy 0 <= overlap < chunk-size, got overlap={a.overlap}, chunk-size={a.chunk_size}")
    manifest = json.loads(pathlib.Path(a.manifest).read_text(encoding="utf-8"))
    ont = yaml.safe_load(pathlib.Path(a.ontology).read_text(encoding="utf-8"))
    ws = build_worksheet(manifest, ont, a.chunk_size, a.overlap)
    pathlib.Path(a.out).write_text(json.dumps(ws, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
