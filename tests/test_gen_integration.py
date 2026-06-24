# tests/test_gen_integration.py
import json, pathlib, shutil, subprocess, sys
import acquire, ontology, generate
from graphify_backend import GraphifyBackend
import normalize, ledger, compile as compiler   # from compiling-graphify-wiki

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "source-sample"
ONT = ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "ontology-sample.yaml"
SAMPLE = ROOT / "fixtures" / "graph-sample.json"
LINT = ROOT / "skills" / "llm-wiki" / "scripts" / "lint.py"

def _fake_graphify(raw_dir):
    def fake_run(cmd, *a, **k):
        assert cmd[1:4] == ["-m", "graphify", "extract"], cmd
        out = pathlib.Path(raw_dir) / "graphify-out"; out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SAMPLE, out / "graph.json")
        class R: returncode = 0; stdout = ""; stderr = ""
        return R()
    return fake_run

def test_source_to_graph_to_lint_clean_wiki(tmp_path):
    # acquire the synthetic source corpus
    raw = tmp_path / "raw"
    manifest = acquire.acquire([str(SRC)], str(raw))
    assert manifest["files"]
    # generate graph.json via the graphify backend (offline fake runner)
    ont = ontology.load_ontology(str(ONT))
    gpath = tmp_path / "graph.json"; rpath = tmp_path / "report.json"
    result = generate.generate_graph(manifest, ont, GraphifyBackend(), str(gpath), str(rpath),
                                      run=_fake_graphify(str(raw)))
    assert result["report"]["result"] == "pass", result["report"]["findings"]
    assert gpath.exists()
    # HANDOFF: compile the generated graph through compiling-graphify-wiki, lint must be clean
    raw_graph = json.loads(gpath.read_text(encoding="utf-8"))
    snap = normalize.normalize(raw_graph, "snap", "2026-06-24T00:00:00Z")
    led = ledger.build_ledger(snap, "led")
    wiki = tmp_path / "wiki"
    compiler.compile_wiki(snap, led, str(wiki), "2026-06-24")
    proc = subprocess.run([sys.executable, str(LINT), str(wiki)], capture_output=True, text=True)
    assert "0 finding(s)." in proc.stdout, proc.stdout
