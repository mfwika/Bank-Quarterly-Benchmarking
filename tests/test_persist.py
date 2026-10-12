import base64
import json
import urllib.error

from bankbench import persist


def test_merge_learned_keeps_both_sides():
    a = {"BS": {"kas": ["cash"]}, "_recipes": {"BCA": {"10": [1]}}}
    b = {"BS": {"kas": ["cash", "cash on hand"], "giro": ["current account"]}, "_recipes": {"BNI": {"5": [2]}}}
    m = persist.merge_learned(a, b)
    assert m["BS"]["kas"] == ["cash", "cash on hand"]
    assert m["BS"]["giro"] == ["current account"]
    assert set(m["_recipes"]) == {"BCA", "BNI"}
    assert a["BS"]["kas"] == ["cash"]  # input tidak berubah


def test_remote_config_requires_token_and_repo():
    assert persist.remote_config({}) is None
    assert persist.remote_config({"mappings_github": {"repo": "a/b"}}) is None
    cfg = persist.remote_config({"mappings_github": {"repo": "a/b", "token": "t"}})
    assert cfg["path"] == "mappings.json"

    class Broken:
        def get(self, k):
            raise FileNotFoundError

    assert persist.remote_config(Broken()) is None


def test_save_remote_merges_with_remote_and_retries_on_conflict(monkeypatch):
    store = {"data": {"BS": {"kas": ["cash"]}}, "sha": "s1", "puts": 0}

    def fake(cfg, method, url, body=None):
        if method == "GET":
            return {"content": base64.b64encode(json.dumps(store["data"]).encode()).decode(), "sha": store["sha"]}
        store["puts"] += 1
        if store["puts"] == 1:  # pengguna lain menyimpan duluan
            store["data"] = {"BS": {"kas": ["cash"], "giro": ["demand deposit"]}}
            store["sha"] = "s2"
            raise urllib.error.HTTPError(url, 409, "conflict", {}, None)
        assert body["sha"] == "s2"
        store["data"] = json.loads(base64.b64decode(body["content"]))
        return {}

    monkeypatch.setattr(persist, "_request", fake)
    out = persist.save_remote({"repo": "a/b", "token": "t", "path": "mappings.json"},
                              {"BS": {"kas": ["kas tunai"]}})
    assert out["BS"]["kas"] == ["cash", "kas tunai"]
    assert out["BS"]["giro"] == ["demand deposit"]
    assert store["data"] == out


def test_load_remote_missing_file(monkeypatch):
    def fake(cfg, method, url, body=None):
        raise urllib.error.HTTPError(url, 404, "nf", {}, None)

    monkeypatch.setattr(persist, "_request", fake)
    assert persist.load_remote({"repo": "a/b", "token": "t", "path": "m.json"}) == ({}, None)
