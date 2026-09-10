import io
import re
import copy
from datetime import datetime

import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.formula.translate import Translator

try:
    from rapidfuzz import fuzz
    def similarity(a: str, b: str) -> float:
        return fuzz.token_sort_ratio(a, b)
except ImportError:
    import difflib
    def similarity(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a, b).ratio() * 100

try:
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


st.set_page_config(page_title="Auto-Update Template Benchmarking", layout="wide")
st.title("Auto-Update Template Benchmarking")
st.caption(
    "Upload laporan keuangan terbaru + template -> sistem cocokkan akun -> "
    "kamu konfirmasi -> sistem update template dengan kolom periode baru."
)


# ---------------------------------------------------------------------------------
# STEP 1-2: UPLOAD
# ---------------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    source_file = st.file_uploader(
        "1. Drag & drop laporan keuangan TERBARU (Excel atau PDF)",
        type=["xlsx", "xls", "pdf"],
    )
with col2:
    template_file = st.file_uploader(
        "2. Drag & drop TEMPLATE yang mau di-update (Excel)",
        type=["xlsx"],
    )

if not source_file or not template_file:
    st.info("Upload kedua file dulu untuk lanjut.")
    st.stop()


# ---------------------------------------------------------------------------------
# HELPER: cari baris header periode (baris yang berisi banyak label seperti "Mar 24")
# ---------------------------------------------------------------------------------
PERIOD_PATTERN = re.compile(
    r"(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)[a-z]*\s*'?\d{2,4}",
    re.IGNORECASE,
)


def looks_like_period(value) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    return bool(PERIOD_PATTERN.search(s)) and len(s) <= 15


def find_header_row(ws, max_scan_rows=40, max_scan_cols=60):
    """Cari baris yang paling banyak mengandung label periode (mis. 'Mar 24')."""
    best_row, best_count = None, 0
    for r in range(1, min(max_scan_rows, ws.max_row) + 1):
        count = 0
        for c in range(1, min(max_scan_cols, ws.max_column) + 1):
            if looks_like_period(ws.cell(r, c).value):
                count += 1
        if count > best_count:
            best_row, best_count = r, count
    return best_row, best_count


def find_label_column(ws, header_row, sample_rows=200):
    """
    Cari kolom teks (label akun) di sebelah kiri kolom-kolom angka.
    Ambil kolom paling KANAN di antara kolom-kolom teks (biasanya label paling
    detail/spesifik ada di kolom paling kanan sebelum kolom angka, sesuai pola
    'No. | (indent kosong) | label' pada template acuan).
    """
    text_cols = []
    for c in range(1, ws.max_column + 1):
        text_hits, total = 0, 0
        for r in range(header_row + 1, min(header_row + 1 + sample_rows, ws.max_row) + 1):
            v = ws.cell(r, c).value
            if v is None:
                continue
            total += 1
            if isinstance(v, str) and not looks_like_period(v):
                text_hits += 1
        if total > 0 and text_hits / total > 0.6 and text_hits >= 3:
            text_cols.append(c)
    return max(text_cols) if text_cols else None


def find_last_period_column(ws, header_row):
    last_col = None
    for c in range(1, ws.max_column + 1):
        if looks_like_period(ws.cell(header_row, c).value):
            last_col = c
    return last_col


# ---------------------------------------------------------------------------------
# PARSE TEMPLATE
# ---------------------------------------------------------------------------------
tpl_bytes = template_file.read()
wb = openpyxl.load_workbook(io.BytesIO(tpl_bytes), data_only=False)

sheet_name = st.selectbox("Pilih sheet template yang mau di-update:", wb.sheetnames)
ws = wb[sheet_name]

header_row, header_hits = find_header_row(ws)
if header_row is None or header_hits == 0:
    st.error(
        "Tidak menemukan baris header periode (mis. 'Mar 24') di sheet ini. "
        "Coba pilih sheet lain, atau cek format template."
    )
    st.stop()

label_col = find_label_column(ws, header_row)
last_period_col = find_last_period_column(ws, header_row)

if label_col is None or last_period_col is None:
    st.error("Gagal mendeteksi kolom label akun / kolom periode terakhir di sheet ini.")
    st.stop()

st.success(
    f"Terdeteksi: baris header periode = baris {header_row}, "
    f"kolom label akun = {get_column_letter(label_col)}, "
    f"kolom periode terakhir = {get_column_letter(last_period_col)} "
    f"('{ws.cell(header_row, last_period_col).value}')."
)

new_period_label = st.text_input(
    "Label periode baru untuk kolom yang akan ditambahkan (mis. 'Sep 25'):",
    value="",
)

# Kumpulkan baris-baris akun di template (dari bawah header sampai baris kosong panjang)
template_rows = []
empty_streak = 0
r = header_row + 1
while r <= ws.max_row and empty_streak < 15:
    label = ws.cell(r, label_col).value
    prev_val = ws.cell(r, last_period_col).value
    if label is None and prev_val is None:
        empty_streak += 1
    else:
        empty_streak = 0
        if label is not None and str(label).strip() != "":
            template_rows.append(
                {
                    "row": r,
                    "label": str(label).strip(),
                    "prev_value": prev_val,
                    "is_formula": isinstance(prev_val, str) and str(prev_val).startswith("="),
                }
            )
    r += 1

if not template_rows:
    st.error("Tidak ada baris akun terbaca di bawah header. Cek deteksi kolom label.")
    st.stop()


# ---------------------------------------------------------------------------------
# PARSE SOURCE (laporan keuangan baru) -> list of (label, value)
# ---------------------------------------------------------------------------------
def parse_source_excel(file_bytes):
    swb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    pairs = []
    for sn in swb.sheetnames:
        sws = swb[sn]
        for row in sws.iter_rows():
            label, values = None, []
            for cell in row:
                v = cell.value
                if v is None:
                    continue
                if isinstance(v, str) and not looks_like_period(v):
                    if label is None or len(v.strip()) > len(label):
                        label = v.strip()
                elif isinstance(v, (int, float)):
                    values.append(v)
            if label and values:
                pairs.append((label, values[0]))
    return pairs


def parse_source_pdf(file_bytes):
    pairs = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cells = [c for c in row if c is not None and str(c).strip() != ""]
                    if len(cells) < 2:
                        continue
                    label = str(cells[0]).strip()
                    if looks_like_period(label) or label == "":
                        continue
                    value = None
                    for c in cells[1:]:
                        c_clean = str(c).replace(".", "").replace(",", "").replace("(", "-").replace(")", "").strip()
                        try:
                            value = float(c_clean)
                            break
                        except ValueError:
                            continue
                    if value is not None:
                        pairs.append((label, value))
    return pairs


src_bytes = source_file.read()
if source_file.name.lower().endswith(".pdf"):
    if not HAS_PDF:
        st.error("pdfplumber belum terinstall. Jalankan: pip install pdfplumber")
        st.stop()
    source_pairs = parse_source_pdf(src_bytes)
else:
    source_pairs = parse_source_excel(src_bytes)

if not source_pairs:
    st.error("Tidak ada data (label + angka) yang berhasil diekstrak dari laporan baru.")
    st.stop()

st.caption(f"{len(source_pairs)} baris akun terbaca dari laporan keuangan baru.")


# ---------------------------------------------------------------------------------
# STEP 3: MATCHING (fuzzy) — hanya untuk baris yang BUKAN formula
# ---------------------------------------------------------------------------------
SCORE_THRESHOLD = 80  # di bawah ini, tidak auto-pilih -> user harus pilih manual

source_labels = [p[0] for p in source_pairs]

review_rows = []
for tr in template_rows:
    if tr["is_formula"]:
        review_rows.append(
            {
                "Baris Template": tr["row"],
                "Akun (Template)": tr["label"],
                "Tipe": "FORMULA (auto-geser)",
                "Akun Cocok (Laporan Baru)": "-",
                "Nilai": "-",
                "Skor": "-",
            }
        )
        continue

    scored = sorted(
        ((similarity(tr["label"], sl), sl, sv) for sl, sv in source_pairs),
        key=lambda x: x[0],
        reverse=True,
    )
    best_score, best_label, best_value = scored[0] if scored else (0, "", None)

    review_rows.append(
        {
            "Baris Template": tr["row"],
            "Akun (Template)": tr["label"],
            "Tipe": "Nilai",
            "Akun Cocok (Laporan Baru)": best_label if best_score >= SCORE_THRESHOLD else "(pilih manual)",
            "Nilai": best_value if best_score >= SCORE_THRESHOLD else None,
            "Skor": round(best_score, 1),
        }
    )

review_df = pd.DataFrame(review_rows)

# ---------------------------------------------------------------------------------
# STEP 4: TABEL KONFIRMASI (WAJIB dicek user sebelum apply)
# ---------------------------------------------------------------------------------
st.subheader("Konfirmasi hasil matching sebelum ditulis ke template")
st.caption(
    "Baris dengan skor rendah / '(pilih manual)' HARUS diisi/dikoreksi manual dulu "
    "(edit langsung di kolom 'Akun Cocok' dan 'Nilai'). Baris FORMULA tidak butuh angka; "
    "formula akan otomatis mengikuti pola kolom sebelumnya."
)

edited_df = st.data_editor(
    review_df,
    use_container_width=True,
    num_rows="fixed",
    disabled=["Baris Template", "Akun (Template)", "Tipe", "Skor"],
    key="review_editor",
)

low_conf = edited_df[
    (edited_df["Tipe"] == "Nilai")
    & ((edited_df["Skor"] == "-") | (pd.to_numeric(edited_df["Skor"], errors="coerce") < SCORE_THRESHOLD))
]
if len(low_conf) > 0:
    st.warning(
        f"{len(low_conf)} baris masih perlu dicek/dilengkapi manual sebelum apply "
        "(skor kemiripan di bawah ambang batas atau belum ada match)."
    )

st.divider()


# ---------------------------------------------------------------------------------
# STEP 5: APPLY -> tambah kolom baru di template
# ---------------------------------------------------------------------------------
def copy_cell_style(src_cell, dst_cell):
    dst_cell.font = copy.copy(src_cell.font)
    dst_cell.border = copy.copy(src_cell.border)
    dst_cell.fill = copy.copy(src_cell.fill)
    dst_cell.number_format = copy.copy(src_cell.number_format)
    dst_cell.alignment = copy.copy(src_cell.alignment)
    dst_cell.protection = copy.copy(src_cell.protection)


def shift_formula(formula: str, src_col: int, dst_col: int, row: int) -> str:
    src_coord = f"{get_column_letter(src_col)}{row}"
    dst_coord = f"{get_column_letter(dst_col)}{row}"
    return Translator(formula, origin=src_coord).translate_formula(dst_coord)


apply_clicked = st.button("Terapkan ke Template", type="primary", disabled=not new_period_label.strip())
if not new_period_label.strip():
    st.info("Isi dulu label periode baru di atas (mis. 'Sep 25') untuk mengaktifkan tombol apply.")

if apply_clicked:
    new_col = last_period_col + 1

    # copy lebar kolom & style header dari kolom periode terakhir
    ws.column_dimensions[get_column_letter(new_col)].width = ws.column_dimensions[
        get_column_letter(last_period_col)
    ].width

    header_src = ws.cell(header_row, last_period_col)
    header_dst = ws.cell(header_row, new_col)
    header_dst.value = new_period_label.strip()
    copy_cell_style(header_src, header_dst)

    edited_lookup = {row["Baris Template"]: row for row in edited_df.to_dict("records")}

    applied, skipped = 0, 0
    for tr in template_rows:
        row_num = tr["row"]
        src_cell = ws.cell(row_num, last_period_col)
        dst_cell = ws.cell(row_num, new_col)
        copy_cell_style(src_cell, dst_cell)

        info = edited_lookup.get(row_num)

        if tr["is_formula"]:
            dst_cell.value = shift_formula(str(tr["prev_value"]), last_period_col, new_col, row_num)
            applied += 1
        else:
            val = info["Nilai"] if info else None
            if val in (None, "", "-"):
                skipped += 1
                continue
            try:
                dst_cell.value = float(val)
            except (TypeError, ValueError):
                dst_cell.value = val
            applied += 1

    st.success(f"Selesai. {applied} baris terisi, {skipped} baris dilewati (belum ada nilai).")

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)

    fname = f"{template_file.name.rsplit('.', 1)[0]}_updated_{datetime.now().strftime('%Y%m%d')}.xlsx"
    st.download_button(
        "Download template hasil update",
        data=out,
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )