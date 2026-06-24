#!/usr/bin/env python3
"""Compile a canonical snapshot + claim ledger into an llm-wiki-format wiki.
Every graphify node -> one concept page; sources -> source pages; communities -> map pages."""
import argparse, json, sys, pathlib, re, yaml
import scaffold

_UNSAFE = re.compile(r'[/\\:*?"<>|]')

# Inline (flow-style) YAML list — renders as [a, b] not multi-line "- a\n- b"
class _Inline(list):
    pass

class _SafeDumperWithInline(yaml.SafeDumper):
    pass

_SafeDumperWithInline.add_representer(
    _Inline,
    lambda dumper, data: dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True),
)

def _safe(title):
    return _UNSAFE.sub("-", title).strip()

def _src_title(snapshot, source_id):
    for s in snapshot["sources"]:
        if s["source_id"] == source_id:
            return _safe(s["title"])
    return _safe(source_id)

def _neighbors(snapshot, node_id):
    titles = {n["id"]: _safe(n["title"]) for n in snapshot["nodes"]}
    out = []
    for e in snapshot["edges"]:
        if e["source"] == node_id and e["target"] in titles:
            out.append(titles[e["target"]])
        elif e["target"] == node_id and e["source"] in titles:
            out.append(titles[e["source"]])
    return sorted(set(out))

def _claims_for(ledger, node_id):
    return [c for c in ledger["claims"] if c.get("node_id") == node_id]

def _fm(d):
    return "---\n" + yaml.dump(d, Dumper=_SafeDumperWithInline, sort_keys=False, allow_unicode=True) + "---\n"

def _claim_line(snapshot, claim, neighbors):
    text = claim["text"].rstrip(".")
    if claim.get("source_ids"):
        src = _src_title(snapshot, claim["source_ids"][0])
        loc = claim.get("source_location") or "source"
        return f'- {text}.^[from [[{src}]] — "{loc}"]'
    if neighbors:
        return f'- {text}. Related: [[{neighbors[0]}]]'
    return f'- {text}.  <!-- claim:{claim["claim_id"]} unsourced -->'

def _concept_page(snapshot, ledger, node, date):
    title = _safe(node["title"])
    claims = _claims_for(ledger, node["id"])
    neighbors = _neighbors(snapshot, node["id"])
    src_titles = sorted({_src_title(snapshot, s) for s in node.get("source_ids", [])})
    fm = {"type": "concept", "aliases": _Inline(node.get("aliases", [])),
          "tags": _Inline(node.get("tags", []) or ["concept"]),
          "created": date, "updated": date, "status": "draft",
          "related": [f"[[{n}]]" for n in neighbors],
          "sources": [f"[[{s}]]" for s in src_titles],
          "claim_ids": _Inline([c["claim_id"] for c in claims]),
          "graphify_nodes": _Inline([node["id"]])}
    lines = [_fm(fm), f"# {title}\n", "## Claims"]
    for c in claims:
        lines.append(_claim_line(snapshot, c, neighbors))
    lines.append("\n## Related")
    for nb in neighbors:
        lines.append(f"- [[{nb}]]")
    for s in src_titles:
        lines.append(f"- [[{s}]]")
    if not neighbors and not src_titles:
        lines.append("- [[overview]]")
    return title, "\n".join(lines) + "\n"

def _source_page(source, date):
    title = _safe(source.get("title") or source["source_id"])
    fm = {"type": "source", "aliases": [], "tags": ["source"], "created": date, "updated": date,
          "status": "draft", "url": source.get("uri", ""), "source_type": "webpage", "covers": []}
    return title, _fm(fm) + f"# {title}\n\n## Summary\n\nSource `{source['source_id']}` ingested for graphify compilation.\n"

def _map_page(snapshot, comm, date):
    title = _safe(comm["title"])
    members = [_safe(n["title"]) for n in snapshot["nodes"] if n["id"] in comm.get("member_node_ids", [])]
    fm = {"type": "map", "tags": ["moc"], "created": date, "updated": date, "status": "draft"}
    body = [f"# {title}\n", "## Members"] + [f"- [[{m}]]" for m in members]
    return title, _fm(fm) + "\n".join(body) + "\n"

def _register(index_path, title, desc):
    text = index_path.read_text(encoding="utf-8")
    if f"[[{title}]]" not in text:
        index_path.write_text(text.rstrip() + f"\n- [[{title}]] — {desc}\n", encoding="utf-8")

def compile_wiki(snapshot, ledger, out_root, date):
    scaffold.scaffold(out_root, "compiled from a Graphify graph", date)
    root = pathlib.Path(out_root)
    for s in snapshot["sources"]:
        title, text = _source_page(s, date)
        (root / "wiki" / "sources" / f"{title}.md").write_text(text, encoding="utf-8")
        _register(root / "wiki" / "sources" / "_index.md", title, (s.get("uri") or "source"))
    for node in snapshot["nodes"]:
        title, text = _concept_page(snapshot, ledger, node, date)
        (root / "wiki" / "concepts" / f"{title}.md").write_text(text, encoding="utf-8")
        _register(root / "wiki" / "concepts" / "_index.md", title, title)
    for comm in snapshot["communities"]:
        title, text = _map_page(snapshot, comm, date)
        (root / "wiki" / "maps" / f"{title}.md").write_text(text, encoding="utf-8")
    return None

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default="2026-06-24")
    a = ap.parse_args(argv)
    snap = json.loads(open(a.snapshot, encoding="utf-8").read())
    led = yaml.safe_load(open(a.ledger, encoding="utf-8").read())
    compile_wiki(snap, led, a.out, a.date)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
