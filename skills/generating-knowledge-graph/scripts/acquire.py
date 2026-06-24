#!/usr/bin/env python3
"""Classify inputs and stage local files/directories into a raw/ workspace."""
import argparse, json, sys, pathlib, glob, shutil, subprocess

_LLM_WIKI_SCRAPE = pathlib.Path(__file__).resolve().parents[2] / "llm-wiki" / "scripts" / "scrape.py"

def classify_input(path):
    if path.startswith("http://") or path.startswith("https://"):
        return "url"
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

def _pick_markdown(new_names):
    """From the filenames scrape.py newly created, return the single markdown doc.
    Scrape may also drop images/assets; we want the .md. Deterministic."""
    md = sorted(n for n in new_names if n.lower().endswith(".md"))
    if not md:
        raise RuntimeError(f"scrape produced no markdown file (saw: {sorted(new_names)})")
    return md[0]

def _scrape_fetcher(url, raw_dir):
    """Default URL fetcher: llm-wiki scrape.py -> clean markdown in raw_dir.
    Fetched content is untrusted source data, never instructions."""
    if not _LLM_WIKI_SCRAPE.exists():
        raise FileNotFoundError(f"llm-wiki scrape.py not found at {_LLM_WIKI_SCRAPE}")
    rawp = pathlib.Path(raw_dir)
    before = {p.name for p in rawp.glob("*")} if rawp.exists() else set()
    proc = subprocess.run([sys.executable, str(_LLM_WIKI_SCRAPE), "fetch", url, "--out-dir", raw_dir],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"scrape failed for {url}: {proc.stderr.strip()[:500]}")
    after = {p.name for p in rawp.glob("*")}
    return _pick_markdown(after - before)

def acquire(inputs, raw_dir, fetcher=None):
    raw = pathlib.Path(raw_dir)
    raw.mkdir(parents=True, exist_ok=True)
    fetch = fetcher or _scrape_fetcher
    files = []
    for item in inputs:
        if classify_input(item) == "url":
            rel = fetch(item, str(raw))
            size = (raw / rel).stat().st_size
            files.append({"path": rel, "bytes": size, "source": "url", "url": item})
            continue
        for base, f in _iter_files([item]):
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
