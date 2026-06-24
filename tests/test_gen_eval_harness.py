# tests/test_gen_eval_harness.py
import json, pathlib, yaml
from llm_backend import LlmBackend
import llm_client, evaluate

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLD = ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "gold"
ONT = yaml.safe_load((ROOT / "skills" / "generating-knowledge-graph" / "fixtures" / "ontology-sample.yaml").read_text(encoding="utf-8"))

def test_cassette_backend_scores_perfect_against_gold(tmp_path):
    raw = tmp_path / "raw"; raw.mkdir()
    (raw / "source.md").write_text((GOLD / "source.md").read_text(encoding="utf-8"), encoding="utf-8")
    manifest = {"raw_dir": str(raw), "files": [{"path": "source.md", "bytes": 50}]}
    responses = json.loads((GOLD / "cassette.json").read_text(encoding="utf-8"))
    backend = LlmBackend(llm_client.CassetteClient(responses), chunk_size=10000)
    graph = backend.generate(manifest, ONT, str(tmp_path / "g.json"))
    gold = json.loads((GOLD / "gold-graph.json").read_text(encoding="utf-8"))
    s = evaluate.score(graph, gold)
    assert s["entities"]["f1"] == 1.0, s
    assert s["relations"]["f1"] == 1.0, s
