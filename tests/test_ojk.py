import os

import pytest

from bankbench.ojk import _repair_categories, is_ojk_excel, merge_sources
from bankbench.source_parser import parse_source

DIR = os.path.join(os.path.dirname(__file__), "regression", "reports", "ojk_mandiri_jun2026")
J26, J25, D25 = (6, 2026), (6, 2025), (12, 2025)


def _read(name):
    path = os.path.join(DIR, name)
    if not os.path.exists(path):
        pytest.skip("file OJK contoh tidak ada")
    with open(path, "rb") as fh:
        return fh.read()


def test_repair_missing_collectibility_column():
    cols = [(J26, "IND")] * 5 + [(J25, "IND")] * 5
    cats = ["L", "DPK", "KL", "M", "JUMLAH", "L", "DPK", "D", "M", "JUMLAH"]
    vals = [100, 0, 4, 0, 109, 100, 0, 5, 0, 109]  # Jun 26 tanpa D, Jun 25 tanpa KL
    v, c, k = _repair_categories(vals, cols, cats)
    assert dict(zip(zip(c, k), v))[((J26, "IND"), "D")] == 5
    assert dict(zip(zip(c, k), v))[((J25, "IND"), "KL")] == 4


def test_ojk_balance_sheet_headers_and_group():
    data = _read("posisi_keuangan.xlsx")
    assert is_ojk_excel(data)
    rows, text = parse_source("posisi_keuangan.xlsx", data)
    kas = rows[0]
    assert kas.label == "Kas" and kas.section == "BS"
    assert kas.cols == [(J26, "IND"), (D25, "IND"), (J26, "KONS"), (D25, "KONS")]
    assert kas.group == "OJK|PT BANK MANDIRI (PERSERO)|6/2026"
    ckpn_sb = next(r for r in rows if r.label == "Surat berharga yang dimiliki" and r.ancestors)
    assert "Cadangan kerugian" in ckpn_sb.parent
    assert "30 Juni 2026" in text


def test_ojk_kpmm_period_then_entity_header():
    rows, _ = parse_source("kpmm.xlsx", _read("kpmm.xlsx"))
    assert rows[0].section == "CAP"
    assert rows[0].cols == [(J26, "IND"), (J26, "KONS"), (J25, "IND"), (J25, "KONS")]


def test_ojk_files_merge_into_one_source():
    parts = [parse_source(n, _read(n)) for n in ("rasio.xlsx", "laba_rugi.xlsx", "posisi_keuangan.xlsx")]
    rows, text = merge_sources(parts)
    assert [r.idx for r in rows] == list(range(len(rows)))
    assert rows[0].section == "BS"  # Neraca dulu, lalu Laba Rugi, lalu lainnya
    assert {r.group for r in rows} == {"OJK|PT BANK MANDIRI (PERSERO)|6/2026"}


def test_non_ojk_excel_is_not_detected():
    import io

    import openpyxl

    wb = openpyxl.Workbook()
    wb.active["A1"] = "Neraca"
    bio = io.BytesIO()
    wb.save(bio)
    assert not is_ojk_excel(bio.getvalue())
