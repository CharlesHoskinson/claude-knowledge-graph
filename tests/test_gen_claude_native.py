# tests/test_gen_claude_native.py
import json, pathlib, subprocess, sys, yaml
import acquire, prep, generate
import normalize, ledger, compile as compiler

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "skills" / "generating-knowledge-graph"
SRC = GEN / "fixtures" / "source-llm"                 # single-chunk doc.md from G2
ONT_PATH = GEN / "fixtures" / "ontology-sample.yaml"
ONT = yaml.safe_load(ONT_PATH.read_text(encoding="utf-8"))
CASS = GEN / "fixtures" / "cassette-llm.json"          # [entities, relations] for that doc
LINT = ROOT / "skills" / "llm-wiki" / "scripts" / "lint.py"

def test_claude_native_flow_no_ollama(tmp_path):
    # 1. acquire the source
    raw = tmp_path / "raw"
    manifest = acquire.acquire([str(SRC)], str(raw))
    mpath = tmp_path / "m.json"; mpath.write_text(json.dumps(manifest), encoding="utf-8")
    # 2. prep the worksheet (Claude would read this); assert one entry per chunk
    ws = prep.build_worksheet(manifest, ONT, chunk_size=10000)
    assert len(ws) == 1 and ws[0]["entity_types"]
    # 3. responses.json = what Claude writes per worksheet entry (here: the fixture cassette)
    responses = json.loads(CASS.read_text(encoding="utf-8"))
    assert len(responses) == 2 * len(ws)              # two responses (entities, relations) per entry
    rpath = tmp_path / "responses.json"; rpath.write_text(json.dumps(responses), encoding="utf-8")
    # 4. assemble via --cassette (no Ollama, no key)
    gpath = tmp_path / "graph.json"; rep = tmp_path / "rep.json"
    rc = generate.main(["--manifest", str(mpath), "--ontology", str(ONT_PATH), "--backend", "llm",
                        "--cassette", str(rpath), "--out", str(gpath), "--report", str(rep),
                        "--chunk-size", "10000"])
    assert rc == 0
    # 5. handoff: compile and lint
    graph = json.loads(gpath.read_text(encoding="utf-8"))
    snap = normalize.normalize(graph, "snap", "2026-06-24T00:00:00Z")
    led = ledger.build_ledger(snap, "led")
    wiki = tmp_path / "wiki"
    compiler.compile_wiki(snap, led, str(wiki), "2026-06-24")
    proc = subprocess.run([sys.executable, str(LINT), str(wiki)], capture_output=True, text=True)
    assert "0 finding(s)." in proc.stdout, proc.stdout
