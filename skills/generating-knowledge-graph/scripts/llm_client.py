#!/usr/bin/env python3
"""LLM client interface for graph extraction: complete_json(prompt, schema) -> dict.
G2 ships an Ollama adapter (non-thinking, temp 0, schema-constrained) and an offline
CassetteClient. The Anthropic adapter is G3."""
import json, urllib.request
import jsonschema

def validate_response(obj, schema):
    jsonschema.validate(obj, schema)
    return obj

class CassetteClient:
    """Returns recorded responses in call order — offline, deterministic."""
    def __init__(self, responses):
        self._responses = list(responses)
        self._i = 0
    def __call__(self, prompt, schema):
        r = self._responses[self._i]
        self._i += 1
        return r

def _urllib_post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def make_ollama_client(model="qwen2.5-32b-instruct", host="http://localhost:11434",
                       num_ctx=8192, http_post=None):
    post = http_post or _urllib_post
    def client(prompt, schema):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "format": schema,                       # grammar-constrained JSON
            "stream": False,
            "think": False,                         # non-thinking (strict JSON)
            "options": {"temperature": 0, "num_ctx": num_ctx},
        }
        raw = post(f"{host}/api/chat", payload)
        return json.loads(raw["message"]["content"])
    return client
