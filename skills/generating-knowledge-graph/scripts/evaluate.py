#!/usr/bin/env python3
"""Score a predicted node-link graph against a labeled gold graph."""
import argparse, json, sys, pathlib

def _norm(s):
    return str(s).strip().lower()

def _prf(pred, gold):
    tp = len(pred & gold)
    precision = tp / len(pred) if pred else (1.0 if not gold else 0.0)
    recall = tp / len(gold) if gold else (1.0 if not pred else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}

def score(predicted, gold):
    label = {n["id"]: _norm(n.get("label", n["id"])) for n in predicted.get("nodes", [])}
    # entities/relations matched case-insensitively (name, type, predicate all normalized)
    pred_entities = {(_norm(n.get("label", n["id"])), _norm(n.get("type", ""))) for n in predicted.get("nodes", [])}
    gold_entities = {(_norm(e["name"]), _norm(e["type"])) for e in gold.get("entities", [])}
    pred_relations = {(label.get(l["source"], _norm(l["source"])), _norm(l["relation"]),  # fall back to the raw (normalized) id if a link endpoint isn't a known node
                       label.get(l["target"], _norm(l["target"]))) for l in predicted.get("links", [])}
    gold_relations = {(_norm(r["source"]), _norm(r["predicate"]), _norm(r["target"])) for r in gold.get("relations", [])}
    return {"entities": _prf(pred_entities, gold_entities),
            "relations": _prf(pred_relations, gold_relations)}

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--predicted", required=True)
    ap.add_argument("--gold", required=True)
    a = ap.parse_args(argv)
    predicted = json.loads(pathlib.Path(a.predicted).read_text(encoding="utf-8"))
    gold = json.loads(pathlib.Path(a.gold).read_text(encoding="utf-8"))
    print(json.dumps(score(predicted, gold), indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
