"""Cek silang rasio NPL: NPL ÷ (Current + Special Mention + NPL) dibandingkan dengan rasio
NPL gross yang diisi dari tabel rasio laporan. Hanya informasi — definisi bank bisa sedikit
beda (bank saja vs konsolidasian, kredit saja vs termasuk pembiayaan)."""
from __future__ import annotations

import re

_LIT = re.compile(r"^=\s*[\d.+\-*/()\s]+$")


def _num(value, formula):
    if formula and isinstance(formula, str) and _LIT.match(formula):
        try:
            return float(eval(formula[1:], {"__builtins__": {}}, {}))  # hanya angka & operator
        except (SyntaxError, ZeroDivisionError, TypeError):
            return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return None if v != v else v  # NaN


def npl_crosscheck(rows, tol=0.15):
    """rows: iterable dict {section, label, value, formula}. -> dict atau None kalau data kurang."""
    got = {}
    for r in rows:
        sec, lab = r.get("section"), (r.get("label") or "").strip().lower()
        if sec == "NPL":
            key = ("current" if lab.startswith("current") else "special" if lab.startswith("special")
                   else "npl" if lab.startswith("npl") else None)
        elif sec == "RATIO" and re.match(r"npl gross", lab):
            key = "ratio"
        else:
            key = None
        if key and key not in got:
            v = _num(r.get("value"), r.get("formula"))
            if v is not None:
                got[key] = v
    if not all(k in got for k in ("current", "special", "npl", "ratio")):
        return None
    total = got["current"] + got["special"] + got["npl"]
    if total <= 0:
        return None
    calc = got["npl"] / total * 100
    rep = got["ratio"] * 100 if got["ratio"] < 1 else got["ratio"]  # template lama: 0.0181 = 1,81%
    return {"hitung": calc, "laporan": rep, "selisih": calc - rep, "ok": abs(calc - rep) <= tol}
