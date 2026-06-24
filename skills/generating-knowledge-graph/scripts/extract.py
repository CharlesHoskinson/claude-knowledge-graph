#!/usr/bin/env python3
"""Two-stage (KGGen-style) extraction: entities then relations, constrained to the
ontology, merged/deduped across chunks into a typed node-link graph."""
import re
import chunk as chunker
from llm_client import validate_response

ENTITY_SCHEMA = {
    "type": "object", "required": ["entities"],
    "properties": {"entities": {"type": "array", "items": {
        "type": "object", "required": ["name", "type"],
        "properties": {"name": {"type": "string"}, "type": {"type": "string"}}}}}}

RELATION_SCHEMA = {
    "type": "object", "required": ["relations"],
    "properties": {"relations": {"type": "array", "items": {
        "type": "object", "required": ["source", "predicate", "target"],
        "properties": {"source": {"type": "string"}, "predicate": {"type": "string"},
                       "target": {"type": "string"}}}}}}

def slug(name, type_):
    def s(x):
        return re.sub(r"[^a-z0-9]+", "_", x.lower()).strip("_")
    return f"{s(name)}_{s(type_)}"

def _entity_type_line(e):
    line = f"- {e['name']}: {e.get('description', '').strip()}".rstrip(": ").rstrip()
    examples = e.get("examples")
    if examples:
        line += f" (e.g. {', '.join(str(x) for x in examples)})"
    return line

def _relation_type_line(r):
    sig = f"- {r['name']} ({r.get('domain')}->{r.get('range')})"
    desc = r.get("description", "").strip()
    return f"{sig}: {desc}" if desc else sig

def entity_prompt(chunk, ontology):
    types = "\n".join(_entity_type_line(e) for e in ontology.get("entity_types", []))
    return ("Extract entities (including abstract concepts described in prose, not only "
            "proper nouns) from the SOURCE as JSON matching the schema. "
            f"Only use these entity types:\n{types}\n"
            'Schema: {"entities":[{"name":string,"type":string}]}.\n'
            f"SOURCE:\n{chunk}")

def relation_prompt(chunk, entities, ontology):
    preds = "\n".join(_relation_type_line(r) for r in ontology.get("relation_types", []))
    names = ", ".join(sorted({e["name"] for e in entities}))
    return ("Extract relations between the given ENTITIES from the SOURCE as JSON. "
            f"Only use these predicates (shown as predicate (domain->range): description):\n{preds}\n"
            f"source and target must be among: {names}. "
            'Schema: {"relations":[{"source":string,"predicate":string,"target":string}]}.\n'
            f"SOURCE:\n{chunk}")

def extract_graph(text, ontology, client, source_file, chunk_size=1200, overlap=150):
    entity_types = {e["name"] for e in ontology.get("entity_types", [])}
    relation_types = {r["name"] for r in ontology.get("relation_types", [])}
    nodes = {}     # id -> node
    links = {}     # (src_id, predicate, tgt_id) -> link
    drops = {"unknown_predicate": 0, "unresolved_source": 0, "unresolved_target": 0}
    drop_samples = []   # ≤5 dropped triples for diagnostics
    def _record_drop(reason, r):
        drops[reason] += 1
        if len(drop_samples) < 5:
            drop_samples.append({"source": r.get("source"), "predicate": r.get("predicate"),
                                 "target": r.get("target"), "reason": reason})
    for i, ch in enumerate(chunker.chunk_text(text, chunk_size, overlap)):
        loc = f"chunk-{i}"
        ents = validate_response(client(entity_prompt(ch, ontology), ENTITY_SCHEMA), ENTITY_SCHEMA)["entities"]
        kept = [e for e in ents if e["type"] in entity_types]
        name_to_id = {}
        for e in kept:
            nid = slug(e["name"], e["type"])
            name_to_id[e["name"]] = nid
            nodes.setdefault(nid, {"id": nid, "label": e["name"], "type": e["type"],
                                   "source_file": source_file, "source_location": loc})
        rels = validate_response(client(relation_prompt(ch, kept, ontology), RELATION_SCHEMA), RELATION_SCHEMA)["relations"]
        # Relations are resolved CHUNK-LOCALLY: source/target must be entities extracted
        # from THIS chunk. A relation whose endpoint was only seen in a different chunk is
        # dropped by design (KGGen-style); chunk `overlap` mitigates soft-boundary loss.
        for r in rels:
            if r["predicate"] not in relation_types:
                _record_drop("unknown_predicate", r)
                continue
            s_id, t_id = name_to_id.get(r["source"]), name_to_id.get(r["target"])
            if s_id is None:
                _record_drop("unresolved_source", r)
                continue
            if t_id is None:
                _record_drop("unresolved_target", r)
                continue
            key = (s_id, r["predicate"], t_id)
            links.setdefault(key, {"source": s_id, "target": t_id, "relation": r["predicate"],
                                   "type": r["predicate"], "source_file": source_file, "source_location": loc})
    relation_drops = {"total": sum(drops.values()), "by_reason": drops, "sample": drop_samples}
    return {"nodes": list(nodes.values()), "links": list(links.values()),
            "relation_drops": relation_drops}
