# tests/test_gen_evaluate.py
import evaluate

GOLD = {"entities": [{"name": "app", "type": "Module"}, {"name": "db", "type": "Module"}],
        "relations": [{"source": "app", "predicate": "imports", "target": "db"}]}

def _pred(nodes, links):
    return {"nodes": nodes, "links": links}

def test_perfect_match_is_all_ones():
    pred = _pred(
        [{"id": "app_module", "label": "App", "type": "Module"},   # case-insensitive match
         {"id": "db_module", "label": "db", "type": "Module"}],
        [{"source": "app_module", "target": "db_module", "relation": "imports"}])
    s = evaluate.score(pred, GOLD)
    assert s["entities"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert s["relations"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}

def test_missing_entity_lowers_recall_not_precision():
    pred = _pred([{"id": "app_module", "label": "app", "type": "Module"}], [])
    s = evaluate.score(pred, GOLD)
    assert s["entities"]["precision"] == 1.0
    assert s["entities"]["recall"] == 0.5            # 1 of 2 gold entities found

def test_extra_entity_lowers_precision():
    pred = _pred(
        [{"id": "app_module", "label": "app", "type": "Module"},
         {"id": "db_module", "label": "db", "type": "Module"},
         {"id": "ghost_module", "label": "ghost", "type": "Module"}], [])
    s = evaluate.score(pred, GOLD)
    assert s["entities"]["recall"] == 1.0
    assert round(s["entities"]["precision"], 3) == round(2/3, 3)
