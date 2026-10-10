"""Regresi dengan laporan publikasi asli (tests/regression).

    python -m bankbench.regress                # semua laporan di manifest
    python -m bankbench.regress BNI CIMB       # hanya sheet tertentu

DEFECT = cek total yang BEDA + baris wajib isi yang kosong. Target: 0 untuk semua laporan.
"""
from __future__ import annotations

import json
import os
import sys

from .aliases import merged_aliases
from .matcher import reconcile
from .pattern import StrictMatcher
from .source_parser import parse_source
from .template_model import load_bank_models

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG_DIR = os.path.join(ROOT, "tests", "regression")
TEMPLATE = os.path.join(ROOT, "template.xlsx")


def load_manifest():
    with open(os.path.join(REG_DIR, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def report_path(case):
    return os.path.join(REG_DIR, "reports", case["file"])


def run_case(case, models, chained=None):
    """`chained`: {file: (model, hints)} hasil kasus sebelumnya -> kasus dengan "after" memakai
    kolom hasil laporan itu sebagai periode acuan (seperti app memproses file berurutan)."""
    path = report_path(case)
    with open(path, "rb") as fh:
        rows, _ = parse_source(os.path.basename(path), fh.read())
    model, hints = models[case["sheet"]], None
    if case.get("after"):
        if not chained or case["after"] not in chained:
            raise ValueError(f"{case['file']}: jalankan dulu {case['after']}")
        model, hints = chained[case["after"]]
    tc, _ = model.target_col_for(case["month"], case["year"])
    mt = StrictMatcher(model, rows, tc, merged_aliases({}), (case["month"], case["year"]), recipe_hints=hints)
    res = mt.run()
    if chained is not None:
        fv = {r.row: (r.formula or r.value) for r in res if r.kind != "Formula" and (r.formula or r.value is not None)}
        label = model.period_cols.get(tc) or f"{case['month']:02d}/{case['year']}"
        mem = mt.recipe_memory()
        chained[case["file"]] = (model.with_column(tc, label, fv, hints=mem), {int(k): v for k, v in mem.items()})
    vals = {r.row: r.value for r in res if r.value is not None}
    beda = [c for c in reconcile(mt, vals) if c["Status"] == "BEDA"]
    empty = [r for r in res if r.kind == "Nilai" and r.value is None and not r.formula]
    cek = [r for r in res if "CEK" in (r.note or "")]
    return {"beda": beda, "empty": empty, "cek": cek, "results": res}


def main(argv):
    models = load_bank_models(TEMPLATE)
    total = 0
    chained = {}
    for case in load_manifest():
        if argv and case["sheet"] not in argv:
            continue
        if not os.path.exists(report_path(case)) or (case.get("after") and case["after"] not in chained):
            print(f"SKIP {case['file']} (file / laporan acuan tidak ada)")
            continue
        out = run_case(case, models, chained)
        n = len(out["beda"]) + len(out["empty"])
        total += n
        print(f"{case['sheet']} {case['month']}/{case['year']}: DEFECT={n} "
              f"(beda={len(out['beda'])} kosong={len(out['empty'])}) | 🟡CEK={len(out['cek'])}")
        for c in out["beda"]:
            print("   BEDA", c["Baris"], str(c["Total (template)"])[:40], c["Hasil hitung"], c["Di laporan"])
        for r in out["empty"]:
            print("   KOSONG", r.row, r.section, r.label[:40], (r.note or "")[:90])
    print("TOTAL DEFECT", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
