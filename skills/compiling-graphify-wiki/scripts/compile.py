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

def _unique_titles(pairs):
    """Return a stable id->unique_title map for a list of (id, raw_title) pairs.

    If multiple ids share the same sanitized title (compared case-insensitively,
    matching llm-wiki's case-insensitive link resolution), each is disambiguated
    as '{safe_title} ({id})' so filenames remain unique and deterministic on
    case-insensitive filesystems (e.g. Windows).  The disambiguated titles keep
    their original casing; only the collision-grouping key is lowercased.
    """
    from collections import defaultdict
    folded_to_ids = defaultdict(list)
    for nid, raw in pairs:
        folded_to_ids[_safe(raw).lower()].append(nid)

    result = {}
    for nid, raw in pairs:
        safe = _safe(raw)
        if len(folded_to_ids[safe.lower()]) == 1:
            result[nid] = safe
        else:
            result[nid] = _safe(f"{safe} ({nid})")
    return result

def _src_title(source_id, source_titles):
    return source_titles.get(source_id, _safe(source_id))

def _neighbors(snapshot, node_id, node_titles):
    out = []
    for e in snapshot["edges"]:
        if e["source"] == node_id and e["target"] in node_titles:
            out.append(node_titles[e["target"]])
        elif e["target"] == node_id and e["source"] in node_titles:
            out.append(node_titles[e["source"]])
    return sorted(set(out))

def _claims_for(ledger, node_id):
    return [c for c in ledger["claims"] if c.get("node_id") == node_id]

def _fm(d):
    return "---\n" + yaml.dump(d, Dumper=_SafeDumperWithInline, sort_keys=False, allow_unicode=True) + "---\n"

def _claim_line(claim, neighbors, source_titles):
    text = claim["text"].rstrip(".")
    if claim.get("source_ids"):
        src = _src_title(claim["source_ids"][0], source_titles)
        loc = claim.get("source_location") or "source"
        return f'- {text}.^[from [[{src}]] — "{loc}"]'
    if neighbors:
        return f'- {text}. Related: [[{neighbors[0]}]]'
    return f'- {text}.  <!-- claim:{claim["claim_id"]} unsourced -->'

def _concept_page(snapshot, ledger, node, date, node_titles, source_titles):
    title = node_titles[node["id"]]
    claims = _claims_for(ledger, node["id"])
    neighbors = _neighbors(snapshot, node["id"], node_titles)
    src_titles = sorted({_src_title(s, source_titles) for s in node.get("source_ids", [])})
    fm = {"type": "concept", "aliases": _Inline(node.get("aliases", [])),
          "tags": _Inline(node.get("tags", []) or ["concept"]),
          "created": date, "updated": date, "status": "draft",
          "related": [f"[[{n}]]" for n in neighbors],
          "sources": [f"[[{s}]]" for s in src_titles],
          "claim_ids": _Inline([c["claim_id"] for c in claims]),
          "graphify_nodes": _Inline([node["id"]])}
    lines = [_fm(fm), f"# {title}\n", "## Claims"]
    for c in claims:
        lines.append(_claim_line(c, neighbors, source_titles))
    lines.append("\n## Related")
    for nb in neighbors:
        lines.append(f"- [[{nb}]]")
    for s in src_titles:
        lines.append(f"- [[{s}]]")
    if not neighbors and not src_titles:
        lines.append("- [[overview]]")
    return title, "\n".join(lines) + "\n"

def _source_page(source, date, source_titles):
    title = source_titles[source["source_id"]]
    fm = {"type": "source", "aliases": [], "tags": ["source"], "created": date, "updated": date,
          "status": "draft", "url": source.get("uri", ""), "source_type": "webpage", "covers": []}
    return title, _fm(fm) + f"# {title}\n\n## Summary\n\nSource `{source['source_id']}` ingested for graphify compilation.\n"

def _map_page(snapshot, comm, date, node_titles):
    title = _safe(comm["title"])
    members = [node_titles[n["id"]] for n in snapshot["nodes"] if n["id"] in comm.get("member_node_ids", [])]
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
    node_titles = _unique_titles([(n["id"], n["title"]) for n in snapshot["nodes"]])
    source_titles = _unique_titles([(s["source_id"], s.get("title") or s["source_id"]) for s in snapshot["sources"]])
    for s in snapshot["sources"]:
        title, text = _source_page(s, date, source_titles)
        (root / "wiki" / "sources" / f"{title}.md").write_text(text, encoding="utf-8")
        _register(root / "wiki" / "sources" / "_index.md", title, (s.get("uri") or "source"))
    for node in snapshot["nodes"]:
        title, text = _concept_page(snapshot, ledger, node, date, node_titles, source_titles)
        (root / "wiki" / "concepts" / f"{title}.md").write_text(text, encoding="utf-8")
        _register(root / "wiki" / "concepts" / "_index.md", title, title)
    for comm in snapshot["communities"]:
        title, text = _map_page(snapshot, comm, date, node_titles)
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
