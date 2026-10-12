"""Penyimpanan permanen memori pola (mappings.json).

Di Streamlit Cloud disk app hilang setiap restart, jadi memori pola bisa disimpan ke repo GitHub
lewat Contents API. Aktif kalau `st.secrets` berisi:

    [mappings_github]
    token  = "ghp_..."            # fine-grained token: Contents read & write ke repo itu saja
    repo   = "owner/nama-repo"
    branch = "main"               # opsional (default: branch default repo)
    path   = "mappings.json"      # opsional

Tanpa secrets, app tetap jalan dengan file lokal + upload/download manual.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request

API = "https://api.github.com"


def merge_learned(base: dict, extra: dict) -> dict:
    """Gabung dua memori pola tanpa menghapus apa pun: list digabung (unik, urutan dipertahankan),
    dict digabung rekursif, nilai skalar dari `extra` menang."""
    out = json.loads(json.dumps(base or {}))
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge_learned(out[k], v)
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = out[k] + [x for x in v if x not in out[k]]
        else:
            out[k] = json.loads(json.dumps(v))
    return out


def remote_config(secrets) -> dict | None:
    try:
        cfg = dict(secrets.get("mappings_github") or {})
    except Exception:  # st.secrets tanpa file secrets.toml melempar error
        return None
    if not cfg.get("token") or not cfg.get("repo"):
        return None
    cfg.setdefault("path", "mappings.json")
    return cfg


def _request(cfg, method, url, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None)
    req.add_header("Authorization", f"Bearer {cfg['token']}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode() or "{}")


def _url(cfg):
    u = f"{API}/repos/{cfg['repo']}/contents/{cfg['path']}"
    return u + (f"?ref={cfg['branch']}" if cfg.get("branch") else "")


def load_remote(cfg) -> tuple[dict, str | None]:
    """-> (memori, sha). File belum ada -> ({}, None)."""
    try:
        meta = _request(cfg, "GET", _url(cfg))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}, None
        raise
    data = json.loads(base64.b64decode(meta.get("content", "")).decode() or "{}")
    return (data if isinstance(data, dict) else {}), meta.get("sha")


def save_remote(cfg, data: dict, message="Update memori pola (mappings.json)") -> dict:
    """Simpan ke repo. Memori di remote digabung dulu (pengguna lain mungkin menyimpan duluan),
    sekali ulang kalau sha bentrok. -> memori gabungan yang tersimpan."""
    last = None
    for _ in range(2):
        remote, sha = load_remote(cfg)
        merged = merge_learned(remote, data)
        body = {"message": message,
                "content": base64.b64encode(json.dumps(merged, indent=2, ensure_ascii=False,
                                                       sort_keys=True).encode()).decode()}
        if sha:
            body["sha"] = sha
        if cfg.get("branch"):
            body["branch"] = cfg["branch"]
        try:
            _request(cfg, "PUT", f"{API}/repos/{cfg['repo']}/contents/{cfg['path']}", body)
            return merged
        except urllib.error.HTTPError as e:
            if e.code not in (409, 422):
                raise
            last = e
    raise last
