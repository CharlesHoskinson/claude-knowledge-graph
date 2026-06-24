#!/usr/bin/env python3
"""Classify inputs and stage local files/directories into a raw/ workspace."""
import argparse, json, sys, pathlib, glob, shutil

def classify_input(path):
    p = pathlib.Path(path)
    if p.is_dir():
        return "dir"
    if p.suffix.lower() == ".json":
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, dict) and "nodes" in obj and "links" in obj:
                return "graph"
        except (OSError, ValueError):
            pass
    return "file"

def _iter_files(inputs):
    for item in inputs:
        p = pathlib.Path(item)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    yield p, f
        else:
            for match in sorted(glob.glob(item)):
                mp = pathlib.Path(match)
                if mp.is_file():
                    yield mp.parent, mp

def acquire(inputs, raw_dir):
    raw = pathlib.Path(raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    files = []
    for base, f in _iter_files(inputs):
        rel = f.relative_to(base).as_posix() if base in f.parents else f.name
        dest = raw / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, dest)
        files.append({"path": rel, "bytes": f.stat().st_size})
    files.sort(key=lambda x: x["path"])
    return {"raw_dir": str(raw), "files": files}

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    manifest = acquire(a.inputs, a.raw)
    pathlib.Path(a.out).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
