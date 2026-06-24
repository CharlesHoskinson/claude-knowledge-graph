# tests/test_gen_llm_integration.py
import json, pathlib, subprocess, sys, yaml
import acquire, llm_client, graph_validate
from llm_backend import LlmBackend
import normalize, ledger, compile as compiler   # compiling-graphify-wiki

ROOT = pathlib.Path(__file__).resolve().parents[1]
GEN = ROOT / "skills" / "generating-knowledge-graph"
SRC = GEN / "fixtures" / "source-llm"
ONT = yaml.safe_load((GEN / "fixtures" / "ontology-sample.yaml").read_text(encoding="utf-8"))
CASS = json.loads((GEN / "fixtures" / "cassette-llm.json").read_text(encoding="utf-8"))
LINT = ROOT / "skills" / "llm-wiki" / "scripts" / "lint.py"

def test_source_to_typed_graph_to_lint_clean_wiki(tmp_path):
    raw = tmp_path / "raw"
    manifest = acquire.acquire([str(SRC)], str(raw))
    backend = LlmBackend(llm_client.CassetteClient(CASS), chunk_size=10000)
    gpath = tmp_path / "graph.json"
    graph = backend.generate(manifest, ONT, str(gpath))
    # ontology types are ENFORCED for the llm backend and must pass
    report = graph_validate.validate_graph(graph, ONT)
    assert report["result"] == "pass", report["findings"]
    # handoff: compile the typed graph and lint
    snap = normalize.normalize(graph, "snap", "2026-06-24T00:00:00Z")
    led = ledger.build_ledger(snap, "led")
    wiki = tmp_path / "wiki"
    compiler.compile_wiki(snap, led, str(wiki), "2026-06-24")
    proc = subprocess.run([sys.executable, str(LINT), str(wiki)], capture_output=True, text=True)
    assert "0 finding(s)." in proc.stdout, proc.stdout
