import io
import os
import warnings

import openpyxl
import pytest

from bankbench.aliases import merged_aliases
from bankbench.matcher import Matcher, reconcile
from bankbench.periods import detect_report_period, format_period_label, parse_period_label
from bankbench.source_parser import parse_source, split_label_values
from bankbench.template_model import build_sheet_model, grid_from_worksheet, load_bank_models
from bankbench.text import clean_label, parse_number, similarity
from bankbench.writer import apply_to_workbook

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "template.xlsx")


# ---------------------------------------------------------------- text / angka
@pytest.mark.parametrize("raw,expected", [
    ("1.234.567", 1234567), ("(1.234)", -1234), ("1,234,567", 1234567), ("12,50", 12.5),
    ("-", 0.0), ("-5.000", -5000), ("29,69%", 29.69), ("0", 0.0),
])
def test_parse_number(raw, expected):
    assert parse_number(raw) == pytest.approx(expected)


def test_split_label_values_keeps_numbers_inside_label():
    tok, label, vals = split_label_values("II. MODAL PELENGKAP (TIER 2) 9.604.882 (8.923) - 10.110.402")
    assert tok == "II"
    assert label == "MODAL PELENGKAP (TIER 2)"
    assert vals == [9604882, -8923, 0.0, 10110402]


def test_clean_label_and_similarity():
    assert clean_label("K a s") == "kas"
    assert clean_label("a Tahun-tahun lalu") == "tahun tahun lalu"
    # repo vs reverse repo harus dibedakan
    repo = "Surat berharga yang dijual dengan janji dibeli kembali (repo)"
    rev = "Tagihan atas surat berharga yang dibeli dengan janji dijual kembali (reverse repo)"
    assert similarity(repo, repo) > similarity(repo, rev) + 5


def test_periods():
    assert parse_period_label("Sep 25") == (9, 2025)
    assert parse_period_label("Mar 2009") == (3, 2009)
    assert format_period_label(12, 2025, like="Sep 25") == "Dec 25"
    assert detect_report_period("Per 30 September 2025 dan 31 Desember 2024") == (9, 2025)


# ---------------------------------------------------------------- mini template
def _mini_workbook():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BANKX"
    ws["B2"] = "NERACA - Consol"
    ws["F5"] = "BANK XYZ"
    for c, lbl in zip("FGH", ["Jun 25", "Sep 25", "Dec 25"]):
        ws[f"{c}6"] = lbl
    rows = [
        (8, "1", "K a s", 100_000, 110_000),
        (9, "2", "Kredit", None, None),
        (10, "a", "Pinjaman yang diberikan dan piutang", 500_000, 520_000),
        (11, "3", "Aset lainnya", 50_000, 55_000),
    ]
    for r, enum, lbl, v1, v2 in rows:
        ws[f"B{r}" if enum.isdigit() else f"D{r}"] = enum
        ws[f"D{r}" if enum.isdigit() else f"E{r}"] = lbl
        ws[f"F{r}"], ws[f"G{r}"] = v1, v2
    ws["E12"] = "TOTAL ASET"
    ws["F12"], ws["G12"] = "=SUM(F8:F11)", "=SUM(G8:G11)"
    ws["B20"] = "PERHITUNGAN LABA RUGI - Consol"
    ws["B22"], ws["C22"], ws["F22"], ws["G22"] = 1, "Pendapatan Bunga", 7_000, 11_000
    ws["B23"], ws["C23"], ws["F23"], ws["G23"] = 2, "Beban Bunga", 2_000, 3_000
    ws["C24"], ws["F24"], ws["G24"] = "Pendapatan Bunga Bersih", "=+F22-F23", "=+G22-G23"
    ws["B30"] = "KOMITMEN DAN KONTIGENSI - Consol"
    ws["B40"] = "CAPITAL ADEQUACY RATIO - Consol"
    ws["C42"], ws["F42"], ws["G42"] = "Aset Tertimbang Menurut Risiko (ATMR) untuk Risiko Kredit", 400_000, 410_000
    ws["C43"], ws["F43"], ws["G43"] = "Rasio Kewajiban Penyediaan Modal Minimum", "=F42/2", "=G42/2"
    ws["E50"], ws["F50"], ws["G50"] = "ANNUALIZER", "=12/6", "=12/9"
    return wb


def _mini_model(wb):
    return build_sheet_model("BANKX", grid_from_worksheet(wb["BANKX"]))


def test_template_model_sections_and_hierarchy():
    m = _mini_model(_mini_workbook())
    assert set(m.sections) == {"BS", "IS", "CAP"}
    assert m.bank_name == "BANK XYZ"
    rows = {r.row: r for r in m.rows}
    assert rows[10].parent == "Kredit"
    assert m.target_col_for(12, 2025) == (8, True)  # 'Dec 25' sudah ada (kolom H)
    assert m.target_col_for(3, 2026) == (9, False)  # kolom baru
    assert m.special_rows["annualizer"] == 50


def _source_rows(text):
    from bankbench.source_parser import _feed_text, _RowBuilder

    b = _RowBuilder()
    _feed_text(b, text)
    return b.rows


REPORT = """PT BANK X Tbk
LAPORAN POSISI KEUANGAN
Per 31 Desember 2025 dan 31 Desember 2024
1. Kas 90.000 80.000 120.000 95.000
2. Kredit yang diberikan 480.000 400.000 530.000 450.000
3. Aset lainnya 50.000 40.000 56.000 52.000
TOTAL ASET 620.000 520.000 706.000 597.000
LAPORAN LABA RUGI
1. Pendapatan Bunga 10.000 9.000 12.000 11.000
2. Beban Bunga (3.000) (2.500) (3.100) (3.000)
Pendapatan (Beban) Bunga Bersih 7.000 6.500 8.900 8.000
LAPORAN PERHITUNGAN KEWAJIBAN PENYEDIAAN MODAL MINIMUM
ATMR RISIKO KREDIT 390.000 380.000 420.000 410.000
"""


def test_matcher_identifies_accounts_and_column():
    m = _mini_model(_mini_workbook())
    src = _source_rows(REPORT)
    mt = Matcher(m, src, 8, merged_aliases({}))
    res = {r.row: r for r in mt.run()}
    assert mt.layout.cur_idx == 2  # Konsolidasian periode ini
    assert res[8].value == 120_000
    assert res[10].value == 530_000  # 'Kredit yang diberikan' -> sub-baris 'Pinjaman ...'
    assert res[9].value is None  # induk 'Kredit' tidak diisi (hindari dobel hitung)
    assert res[11].value == 56_000
    assert res[23].value == 3_100  # laporan (3.100) -> template simpan beban positif
    assert res[42].value == 420_000
    assert res[12].kind == "Formula"
    checks = {c["Baris"]: c for c in reconcile(mt, {r: x.value for r, x in res.items() if x.value is not None})}
    assert checks[12]["Status"] == "OK"


def test_writer_new_column_extends_formulas():
    wb = _mini_workbook()
    m = _mini_model(wb)
    n = apply_to_workbook(wb, m, 9, "Mar 26", 3, 2026, {8: 1.0, 10: 2.0}, {8: "cek"})
    ws = wb["BANKX"]
    assert n == 2
    assert ws["I6"].value == "Mar 26"
    assert ws["I12"].value == "=SUM(I8:I11)"
    assert ws["I24"].value == "=+I22-I23"
    assert ws["I50"].value == "=12/3"
    assert ws["I8"].comment.text == "cek"


# ---------------------------------------------------------------- mode strict
def _strict_workbook():
    """Kolom: F=Dec 24 (acuan Neraca & YoY), G=Sep 25, H=Dec 25 (tujuan, kosong)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BANKS"
    ws["B2"] = "NERACA - Consol"
    for c, lbl in zip("FGH", ["Dec 24", "Sep 25", "Dec 25"]):
        ws[f"{c}6"] = lbl
    bs = [(8, "1", "K a s", 95_000, 99_000), (9, "2", "Kredit", None, None),
          (10, "a", "Pinjaman yang diberikan dan piutang", 450_000, 500_000),
          # konvensi analis: Aset lainnya = Aset lainnya + Aset keuangan lainnya
          (11, "3", "Aset lainnya", 55_000, 57_000), (12, "4", "Aset baru", None, None)]
    for r, enum, lbl, v1, v2 in bs:
        ws[f"B{r}" if enum.isdigit() else f"D{r}"] = enum
        ws[f"D{r}" if enum.isdigit() else f"E{r}"] = lbl
        ws[f"F{r}"], ws[f"G{r}"] = v1, v2
    ws["E13"] = "TOTAL ASET"
    for c in "FGH":
        ws[f"{c}13"] = f"=SUM({c}8:{c}12)"
    ws["B20"] = "PERHITUNGAN LABA RUGI - Consol"
    ws["B22"], ws["C22"], ws["F22"], ws["G22"] = 1, "Pendapatan Bunga", 11_000, 8_000
    ws["B23"], ws["C23"], ws["F23"], ws["G23"] = 2, "Beban Bunga", 3_000, 2_200
    ws["B30"] = "KOMITMEN DAN KONTIGENSI - Consol"
    ws["B40"] = "CAPITAL ADEQUACY RATIO - Consol"
    ws["C42"], ws["F42"], ws["G42"] = "Aset Tertimbang Menurut Risiko (ATMR) untuk Risiko Kredit", 410_000, 415_000
    ws["C43"], ws["F43"], ws["G43"] = "Rasio Kewajiban Penyediaan Modal Minimum", "=F42/2", "=G42/2"
    ws["E60"], ws["F60"], ws["G60"] = "NPL Gross (%)", 1.5, 1.45
    ws["E70"] = "Loan Breakdown (IDR bio) - By Collectibility"
    ws["E71"], ws["F71"], ws["G71"] = "Current", "=(1000+2000)/1000", "=(1050+2100)/1000"
    return wb


STRICT_REPORT = """PT BANK S Tbk
LAPORAN POSISI KEUANGAN
INDIVIDUAL KONSOLIDASIAN
31 Des 2025 31 Des 2024 31 Des 2025 31 Des 2024
1. Kas 90.000 80.000 120.000 95.000
2. Kredit yang diberikan 480.000 400.000 530.000 450.000
3. Aset lainnya 50.000 40.000 56.000 52.000
4. Aset keuangan lainnya 2.000 1.000 4.000 3.000
5. Aset baru 7.000 - 7.000 -
TOTAL ASET 629.000 521.000 717.000 600.000
LAPORAN LABA RUGI
INDIVIDUAL KONSOLIDASIAN
31 Des 2025 31 Des 2024 31 Des 2025 31 Des 2024
1. Pendapatan Bunga 10.000 9.000 12.000 11.000
2. Beban Bunga (3.000) (2.500) (3.100) (3.000)
LAPORAN PERHITUNGAN KEWAJIBAN PENYEDIAAN MODAL MINIMUM
31 Des 2025 31 Des 2024
Individual Konsolidasian Individual Konsolidasian
ATMR RISIKO KREDIT 390.000 420.000 380.000 410.000
RASIO KEUANGAN
31 Des 2025 31 Des 2024
NPL gross 1,40 1,50
LAPORAN KUALITAS ASET PRODUKTIF
INDIVIDUAL
31 Des 2025 31 Des 2024
L DPK KL D M JUMLAH L DPK KL D M JUMLAH
1. Kredit yang diberikan
a. Rupiah 1.100 5 - - - 1.105 1.000 4 - - - 1.004
b. Valuta asing 2.200 - - - - 2.200 2.000 - - - - 2.000
"""


def test_strict_follows_reference_pattern():
    from bankbench.pattern import StrictMatcher

    wb = _strict_workbook()
    m = build_sheet_model("BANKS", grid_from_worksheet(wb["BANKS"]))
    assert [r.label for r in m.extra_rows] == ["NPL Gross (%)", "Current"]
    mt = StrictMatcher(m, _source_rows(STRICT_REPORT), 8, merged_aliases({}), (12, 2025))
    res = {r.row: r for r in mt.run()}
    assert res[8].value == 120_000 and res[8].method == "Pola angka"   # Konsolidasian Des 2025
    assert res[10].value == 530_000
    assert res[11].value == 60_000 and res[11].method == "Pola penjumlahan"  # 56.000 + 4.000
    assert res[11].formula == "=56000+4000"
    # akun baru (kosong di acuan) hanya diisi kalau menutup selisih TOTAL ASET vs laporan -> ditandai CEK
    assert res[12].value == 7_000 and res[12].method == "Penyeimbang" and "CEK" in res[12].note
    assert res[9].value is None
    assert res[22].value == 12_000
    assert res[23].value == 3_100      # pola acuan: beban disimpan positif
    assert res[42].value == 420_000    # KPMM: kolom Konsolidasian 2025 (urutan kolom beda)
    assert res[60].value == 1.4        # rasio: pola YoY
    assert res[71].formula == "=(1100+2200)/1000"  # NPL: komponen dilacak ke tabel kualitas aset


def test_chained_periods_use_previous_result_as_reference():
    from bankbench.pattern import StrictMatcher

    wb = _strict_workbook()
    m = build_sheet_model("BANKS", grid_from_worksheet(wb["BANKS"]))
    m2 = m.with_column(8, "Dec 25", {8: 120_000.0, 10: 530_000.0, 11: 60_000.0})
    assert m2.find_period_col(12, 2025) == 8
    report = STRICT_REPORT.replace("31 Des 2025", "30 Jun 2026").replace("31 Des 2024", "31 Des 2025")
    report = report.replace("120.000 95.000", "130.000 120.000")
    tc, exists = m2.target_col_for(6, 2026)
    assert (tc, exists) == (9, False)
    mt = StrictMatcher(m2, _source_rows(report), tc, merged_aliases({}), (6, 2026))
    res = {r.row: r for r in mt.run()}
    assert res[8].value == 130_000  # pola Kas diambil dari hasil Dec 25 sebelumnya


# ---------------------------------------------------------------- end-to-end (template asli)
@pytest.mark.slow
@pytest.mark.skipif(not os.path.exists(TEMPLATE), reason="template.xlsx tidak ada")
@pytest.mark.parametrize("fmt", ["pdf", "xlsx"])
def test_end_to_end_real_template(tmp_path, fmt):
    pytest.importorskip("reportlab")
    from tests.sample_report import build_report_lines, write_pdf, write_xlsx

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        models = load_bank_models(TEMPLATE)
    m = models["BCA"]
    blocks, expected = build_report_lines(m, 19, 16, 15)  # Sep 25 vs Dec 24 / Sep 24
    path = tmp_path / f"bca.{fmt}"
    (write_pdf if fmt == "pdf" else write_xlsx)(blocks, path)
    rows, text = parse_source(str(path), path.read_bytes())
    mt = Matcher(m, rows, 19, merged_aliases({}))
    res = {r.row: r for r in mt.run()}
    wrong = {r: (e, res[r].value) for r, e in expected.items() if res[r].value is None or abs(res[r].value - e) > 1}
    assert not wrong
    checks = reconcile(mt, {r: x.value for r, x in res.items() if x.value is not None})
    balance = [c for c in checks if c["Total (template)"].startswith("Aset =")]
    assert balance and balance[0]["Status"] == "OK"


def test_recipe_memory_keeps_zero_valued_component():
    """Resep Dec 25: Aset lainnya = Aset lainnya + Aset keuangan lainnya. Di Dec 25 aset
    keuangan lainnya = 0, jadi tanpa memori resep akun itu 'hilang' di periode berikutnya."""
    from bankbench.pattern import StrictMatcher

    wb = _strict_workbook()
    m = build_sheet_model("BANKS", grid_from_worksheet(wb["BANKS"]))
    m2 = m.with_column(8, "Dec 25", {11: 56_000.0}, hints={11: ["Aset lainnya", "Aset keuangan lainnya"]})
    report = """LAPORAN POSISI KEUANGAN
INDIVIDUAL KONSOLIDASIAN
30 Jun 2026 31 Des 2025 30 Jun 2026 31 Des 2025
3. Aset lainnya 50.000 40.000 58.000 56.000
4. Aset keuangan lainnya 2.000 - 5.000 -
"""
    mt = StrictMatcher(m2, _source_rows(report), 9, merged_aliases({}), (6, 2026))
    res = {r.row: r for r in mt.run()}
    assert res[11].value == 63_000 and "resep sama" in res[11].note


def test_fallback_without_reference_column_recognises_accounts_and_balances():
    """Kolom Dec 24 (acuan Neraca) kosong: akun tetap dikenali dari nama + kebiasaan
    penjumlahan, lalu total Neraca diseimbangkan ke laporan. Semua ditandai CEK."""
    from bankbench.pattern import StrictMatcher

    wb = _strict_workbook()
    ws = wb["BANKS"]
    for r in range(8, 13):
        ws[f"F{r}"] = None
    ws["F13"] = None
    m = build_sheet_model("BANKS", grid_from_worksheet(ws))
    mt = StrictMatcher(m, _source_rows(STRICT_REPORT), 8, merged_aliases({}), (12, 2025))
    res = {r.row: r for r in mt.run()}
    assert res[8].value == 120_000 and res[8].method == "Nama akun" and "CEK" in res[8].note
    assert res[10].value == 530_000
    # Aset lainnya + Aset keuangan lainnya (kebiasaan); Aset baru -> baris senama (penyeimbang ke TOTAL ASET 717.000)
    assert res[11].formula == "=56000+4000" and res[11].value == 60_000
    assert res[12].value == 7_000 and res[12].method == "Penyeimbang"
    assert res[22].value == 12_000 and res[22].method == "Pola angka"  # Laba Rugi tetap ikut pola YoY


def test_contra_accounts_follow_template_sign_without_reference():
    from bankbench.pattern import StrictMatcher

    wb = _strict_workbook()
    ws = wb["BANKS"]
    ws["E12"], ws["G12"] = "Akumulasi penyusutan -/-", -900
    for r in range(8, 14):
        ws[f"F{r}"] = None
    m = build_sheet_model("BANKS", grid_from_worksheet(ws))
    report = STRICT_REPORT.replace("5. Aset baru 7.000 - 7.000 -", "5. Akumulasi penyusutan -/- 1.000 - 1.000 -")
    mt = StrictMatcher(m, _source_rows(report), 8, merged_aliases({}), (12, 2025))
    res = {r.row: r for r in mt.run()}
    assert res[12].value == -1_000


def test_balance_repair_puts_new_accounts_on_the_right_side():
    """Akun laporan yang belum dikenal diletakkan sesuai sisinya di laporan (aset / liabilitas)
    ke '... lainnya', hanya kalau kombinasinya persis menutup selisih total."""
    from bankbench.pattern import StrictMatcher

    wb = openpyxl.Workbook()
    ws = wb.active
    ws["B2"] = "NERACA - Consol"
    for c, lbl in zip("FGH", ["Dec 24", "Sep 25", "Dec 25"]):
        ws[f"{c}6"] = lbl
    for r, lbl, v in [(8, "Kas", 100), (9, "Aset lainnya", 50), (12, "Giro", 90), (13, "Liabilitas lainnya", 20),
                      (16, "Modal disetor", 40)]:
        ws[f"C{r}"], ws[f"F{r}"], ws[f"G{r}"] = lbl, v * 1000, v * 1000
    ws["C10"] = "TOTAL ASET"
    ws["C14"] = "TOTAL LIABILITAS"
    ws["C17"] = "TOTAL EKUITAS"
    ws["C18"] = "JUMLAH KEWAJIBAN DAN MODAL"
    for c in "FGH":
        ws[f"{c}10"], ws[f"{c}14"] = f"=SUM({c}8:{c}9)", f"=SUM({c}12:{c}13)"
        ws[f"{c}17"], ws[f"{c}18"] = f"=SUM({c}16:{c}16)", f"={c}14+{c}17"
    report = """LAPORAN POSISI KEUANGAN
INDIVIDUAL KONSOLIDASIAN
31 Des 2025 31 Des 2024 31 Des 2025 31 Des 2024
1. Kas 110.000 100.000 110.000 100.000
2. Aset lainnya 50.000 50.000 50.000 50.000
3. Aset kontrak reasuransi 3.000 - 3.000 -
4. Aset kelompok lepasan 2.000 - 2.000 -
TOTAL ASET 165.000 150.000 165.000 150.000
5. Giro 95.000 90.000 95.000 90.000
6. Liabilitas lainnya 20.000 20.000 20.000 20.000
7. Liabilitas kelompok lepasan 1.000 - 1.000 -
TOTAL LIABILITAS 116.000 110.000 116.000 110.000
8. Modal disetor 49.000 40.000 49.000 40.000
TOTAL EKUITAS 49.000 40.000 49.000 40.000
TOTAL LIABILITAS DAN EKUITAS 165.000 150.000 165.000 150.000
"""
    m = build_sheet_model("Sheet", grid_from_worksheet(ws))
    mt = StrictMatcher(m, _source_rows(report), 8, merged_aliases({}), (12, 2025))
    res = {r.row: r for r in mt.run()}
    assert res[9].value == 55_000 and res[9].formula == "=50000+3000+2000"
    assert res[13].value == 21_000 and "Liabilitas kelompok lepasan" in res[13].note
    checks = reconcile(mt, {r: x.value for r, x in res.items() if x.value is not None})
    assert all(c["Status"] == "OK" for c in checks), checks


def test_stacked_and_side_by_side_headers():
    from bankbench.source_parser import _combine_header, parse_entity_header

    assert parse_entity_header("NO KOMPONEN MODAL Individual Konsolidasian Individual Konsolidasian") == \
        ["IND", "KONS", "IND", "KONS"]
    assert parse_entity_header("Modal Pelengkap bank") is None
    # tanggal milik 2 tabel berdampingan -> tidak boleh ada (periode, entitas) dobel
    assert _combine_header([(6, 2026), (6, 2025), (6, 2026), (6, 2025)], ["IND", "KONS", "IND", "KONS"], 4) == \
        [((6, 2026), "IND"), ((6, 2026), "KONS"), ((6, 2025), "IND"), ((6, 2025), "KONS")]
    text = """LAPORAN LABA RUGI
INDIVIDUAL KONSOLIDASIAN
1 JAN 2025 1 JAN 2025
1 JAN 2026 1 JAN 2026
s/d s/d s/d s/d
30 JUN 2025 30 JUN 2025
30 JUN 2026 30 JUN 2026
1. Pendapatan bunga 37.624 32.607 38.630 33.614
2. Kepentingan non pengendali 53 71
"""
    rows = _source_rows(text)
    assert rows[0].cols == [((6, 2026), "IND"), ((6, 2025), "IND"), ((6, 2026), "KONS"), ((6, 2025), "KONS")]
