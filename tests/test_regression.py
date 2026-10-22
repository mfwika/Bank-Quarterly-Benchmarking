"""Laporan publikasi asli -> 0 defect (BEDA + kosong). Lambat (OCR): jalankan dengan
`pytest -m regression` atau `python -m bankbench.regress`."""
import os

import pytest

from bankbench import regress

CASES = regress.load_manifest()


@pytest.fixture(scope="module")
def models():
    from bankbench.template_model import load_bank_models

    return load_bank_models(regress.TEMPLATE)


@pytest.fixture(scope="module")
def chained():
    return {}


@pytest.mark.regression
@pytest.mark.parametrize("case", CASES, ids=[f"{c['sheet']}-{c['month']}-{c['year']}" for c in CASES])
def test_real_report_zero_defect(case, models, chained):
    if not regress.case_exists(case):
        pytest.skip("laporan tidak ada")
    if case.get("ocr"):
        pytest.importorskip("pytesseract")
    if case.get("after") and case["after"] not in chained:
        pytest.skip(f"laporan acuan {case['after']} tidak diproses")
    out = regress.run_case(case, models, chained)
    assert not out["beda"], [(c["Baris"], c["Hasil hitung"], c["Di laporan"]) for c in out["beda"]]
    assert not out["empty"], [(r.row, r.label, r.note) for r in out["empty"]]
