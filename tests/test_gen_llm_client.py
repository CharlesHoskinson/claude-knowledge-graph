# tests/test_gen_llm_client.py
import json, jsonschema, pytest
import llm_client

SCHEMA = {"type": "object", "required": ["entities"],
          "properties": {"entities": {"type": "array"}}}

def test_validate_response_passes_and_raises():
    assert llm_client.validate_response({"entities": []}, SCHEMA) == {"entities": []}
    with pytest.raises(jsonschema.ValidationError):
        llm_client.validate_response({"wrong": 1}, SCHEMA)

def test_cassette_client_returns_in_order():
    c = llm_client.CassetteClient([{"entities": [1]}, {"entities": [2]}])
    assert c("p1", SCHEMA) == {"entities": [1]}
    assert c("p2", SCHEMA) == {"entities": [2]}
    with pytest.raises(IndexError):
        c("p3", SCHEMA)

def test_ollama_client_builds_nonthinking_constrained_request():
    captured = {}
    def fake_post(url, payload):
        captured["url"] = url
        captured["payload"] = payload
        return {"message": {"content": json.dumps({"entities": [{"name": "x", "type": "T"}]})}}
    client = llm_client.make_ollama_client(model="qwen2.5-32b-instruct", http_post=fake_post)
    out = client("extract entities", SCHEMA)
    assert out == {"entities": [{"name": "x", "type": "T"}]}
    p = captured["payload"]
    assert p["model"] == "qwen2.5-32b-instruct"
    assert p["think"] is False
    assert p["options"]["temperature"] == 0
    assert p["format"] == SCHEMA            # schema-constrained decoding
    assert captured["url"].endswith("/api/chat")
