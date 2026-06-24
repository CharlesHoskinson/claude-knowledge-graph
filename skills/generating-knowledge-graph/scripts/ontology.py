#!/usr/bin/env python3
"""Load and validate ontology.yaml (the extraction + validation contract)."""
import argparse, json, sys, pathlib, yaml, jsonschema

_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "ontology.schema.json"

def load_ontology(path):
    return yaml.safe_load(open(path, encoding="utf-8").read())

def validate_ontology(obj):
    findings = []
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(obj, schema)
    except jsonschema.ValidationError as e:
        findings.append({"severity": "error", "message": str(e.message),
                         "path": "/".join(str(p) for p in e.absolute_path)})
        return findings
    entity_names = {e["name"] for e in obj.get("entity_types", [])}
    for r in obj.get("relation_types", []):
        for endpoint in ("domain", "range"):
            if r.get(endpoint) not in entity_names:
                findings.append({"severity": "error",
                                 "message": f"relation '{r.get('name')}' {endpoint} '{r.get(endpoint)}' is not a declared entity_type",
                                 "path": f"relation_types/{r.get('name')}/{endpoint}"})
    return findings

def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ontology", required=True)
    a = ap.parse_args(argv)
    findings = validate_ontology(load_ontology(a.ontology))
    print(json.dumps(findings, indent=2))
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
