#!/usr/bin/env python3
"""Create an llm-wiki skeleton (mirrors llm-wiki references/operations/init.md)."""
import argparse, pathlib, sys

CATEGORIES = ("sources", "entities", "concepts", "syntheses")

def _w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def scaffold(root, domain, date):
    root = pathlib.Path(root)
    _w(root / "CLAUDE.md",
       f"<!-- llm-wiki: v1 -->\n# {root.name} — wiki schema\n\n**Domain:** {domain}\n\n"
       "LLM-maintained knowledge wiki operated by the `llm-wiki` skill. "
       "Compiled by `compiling-graphify-wiki`.\n\n## Layout\n"
       "- `raw/` immutable sources. `wiki/sources|entities|concepts|syntheses/` pages (+ `_index.md`).\n"
       "- `wiki/maps/` topic MOCs. `wiki/overview.md` root MOC. `index.md` router. `log.md` history.\n")
    _w(root / "index.md",
       f"# {root.name}\n\nRouter to category indexes.\n\n"
       + "".join(f"- [[{c}/_index|{c}]] (0)\n" for c in CATEGORIES))
    _w(root / "log.md", f"# Log\n\n## [{date}] init | {root.name}\n- Created wiki skeleton.\n- Domain: {domain}\n")
    _w(root / ".gitignore", ".obsidian/workspace*.json\n.obsidian/cache\n.trash/\n")
    for c in CATEGORIES:
        _w(root / "wiki" / c / "_index.md",
           f"---\ntype: map\ntags: [moc]\ncreated: {date}\nupdated: {date}\nstatus: draft\n---\n\n# {c}\n\n")
    _w(root / "wiki" / "maps" / ".gitkeep", "")
    _w(root / "wiki" / "overview.md",
       "# Overview\n\n> Thesis placeholder — replace after first ingest.\n")
    _w(root / "raw" / "assets" / ".gitkeep", "")

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--domain", default="compiled from a Graphify graph")
    ap.add_argument("--date", default="2026-06-24")
    a = ap.parse_args(argv)
    scaffold(a.out, a.domain, a.date)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
