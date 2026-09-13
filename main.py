import io
import re
import copy
from datetime import datetime

import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.formula.translate import Translator

def _collapse_spaced_letters(s: str) -> str:
    """'K a s' -> 'Kas'. Beberapa template menaruh nama akun dengan spasi di
    antara tiap huruf (kutipan format lama laporan bank) — ini bikin fuzzy
    matching gagal total kalau tidak dirapikan dulu."""
    tokens = s.split()
    out, buf = [], ""
    for t in tokens:
        if len(t) == 1 and t.isalpha():
            buf += t
        else:
            if buf:
                out.append(buf)
                buf = ""
            out.append(t)
    if buf:
        out.append(buf)
    return " ".join(out)


LEADING_ENUM_PATTERN = re.compile(
    r"^\s*(?:\(?[0-9]{1,3}\)?|\(?[a-zA-Z]\)?|\(?[ivxIVX]{1,6}\)?)[\.\)]\s+"
)


def strip_leading_enumerators(s: str) -> str:
    """Buang nomor/huruf urut di depan label (mis. '1.', 'a.', 'iv.') — dilakukan
    berkali-kali karena kadang ada 2 level sekaligus (jarang, tapi aman dicek)."""
    prev = None
    while prev != s:
        prev = s
        s = LEADING_ENUM_PATTERN.sub("", s)
    return s


def clean_label(s: str) -> str:
    s = strip_leading_enumerators(str(s).strip())
    s = _collapse_spaced_letters(s)
    s = re.sub(r"[^\w\s]", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s


try:
    from rapidfuzz import fuzz

    def similarity(a: str, b: str) -> float:
        a2, b2 = clean_label(a), clean_label(b)
        return max(
            fuzz.token_sort_ratio(a2, b2),
            fuzz.token_set_ratio(a2, b2),
            fuzz.partial_ratio(a2, b2),
        )
except ImportError:
    import difflib

    def similarity(a: str, b: str) -> float:
        a2, b2 = clean_label(a), clean_label(b)
        return difflib.SequenceMatcher(None, a2, b2).ratio() * 100

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
# STEP 1: TEMPLATE — disimpan permanen di backend (tidak upload ulang tiap kali).
# Taruh file template kamu di repo GitHub yang SAMA dengan app.py, dengan nama
# persis "template.xlsx". Kalau nanti mau ganti/update template, tinggal replace
# file itu di repo (commit baru), tanpa perlu ubah kode.
# ---------------------------------------------------------------------------------
import os

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.xlsx")

if not os.path.exists(TEMPLATE_PATH):
    st.error(
        f"File template belum ada di repo. Upload file Excel template kamu ke repo GitHub "
        f"dengan nama persis **template.xlsx** (satu folder dengan app.py), lalu commit — "
        f"nanti Streamlit Cloud otomatis rebuild dan template-nya kebaca dari sana."
    )
    st.stop()


st.caption(f"📌 Template terpasang: `template.xlsx` (di-update terakhir kali file ini di-commit ke repo).")

# ---------------------------------------------------------------------------------
# STEP 2: user tinggal drag & drop laporan keuangan terbaru
# ---------------------------------------------------------------------------------
source_file = st.file_uploader(
    "Drag & drop laporan keuangan TERBARU (Excel atau PDF)",
    type=["xlsx", "xls", "pdf"],
)

if not source_file:
    st.info("Upload laporan keuangan terbaru untuk lanjut.")
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


def get_period_columns(ws, header_row, max_scan_cols=200):
    """Semua kolom di baris header yang isinya label periode (mis. 'Mar 24')."""
    cols = []
    for c in range(1, min(max_scan_cols, ws.max_column) + 1):
        if looks_like_period(ws.cell(header_row, c).value):
            cols.append(c)
    return cols


def row_label(ws, row, label_zone_end_col):
    """
    Ambil label akun untuk satu baris dengan mengambil teks PALING KANAN yang
    ditemukan di antara kolom 1 s.d. sebelum kolom periode pertama. Ini dipakai
    (bukan 1 kolom label yang fix) karena banyak template akuntansi menaruh teks
    di kolom berbeda-beda tergantung level indentasi (mis. akun utama di kolom D,
    sub-akun di kolom E, dst) — jadi kolom label tunggal gampang salah deteksi.
    """
    label = None
    for c in range(1, label_zone_end_col):
        v = ws.cell(row, c).value
        if isinstance(v, str) and v.strip() != "" and not looks_like_period(v):
            label = v.strip()
    return label


def extract_month_year(text):
    m = re.match(r"^\s*([A-Za-z]+)[a-z]*\.?\s*'?\s*(\d{2,4})\s*$", str(text).strip())
    if not m:
        return None
    return m.group(1), m.group(2)


# ---------------------------------------------------------------------------------
# PARSE TEMPLATE (di-cache supaya file besar ini TIDAK diparse ulang setiap kali
# ada interaksi di halaman — ini penyebab utama app terasa lambat sebelumnya)
# ---------------------------------------------------------------------------------
TEMPLATE_MTIME = os.path.getmtime(TEMPLATE_PATH)


@st.cache_data(show_spinner=False)
def read_template_bytes(path, mtime):
    with open(path, "rb") as fh:
        return fh.read()


@st.cache_resource(show_spinner=False)
def load_template_readonly(path, mtime):
    """Workbook ini HANYA untuk dibaca (deteksi, matching, preview) — jangan
    ditulisi, karena objeknya dipakai bersama (cache) lintas sesi/user."""
    with open(path, "rb") as fh:
        return openpyxl.load_workbook(io.BytesIO(fh.read()), data_only=False)


def quick_account_row_count(ws, header_row, first_period_col, cap=20, max_check=500):
    """Hitung cepat berapa banyak baris akun asli di bawah header (berhenti lebih
    awal begitu sudah cukup untuk membuktikan sheet ini valid)."""
    count, empty_streak, checked = 0, 0, 0
    r = header_row + 1
    while r <= ws.max_row and empty_streak < 15 and checked < max_check and count < cap:
        if row_label(ws, r, first_period_col) is not None:
            count += 1
            empty_streak = 0
        else:
            empty_streak += 1
        r += 1
        checked += 1
    return count


@st.cache_data(show_spinner=False)
def list_valid_bank_sheets(path, mtime):
    """Cuma tampilkan sheet yang memang berformat laporan per-bank ASLI: punya
    baris header periode DAN cukup banyak baris akun di bawahnya (>=15). Ini
    menyingkirkan sheet ringkasan/analisis/notes yang kebetulan juga punya
    kolom bertanggal tapi bukan template per-bank."""
    wb_check = load_template_readonly(path, mtime)
    valid = []
    for sn in wb_check.sheetnames:
        wsx = wb_check[sn]
        hr, hits = find_header_row(wsx)
        if hr is None or hits < 3:
            continue
        period_cols = get_period_columns(wsx, hr)
        if not period_cols:
            continue
        if quick_account_row_count(wsx, hr, min(period_cols)) >= 15:
            valid.append(sn)
    return valid


with st.spinner("Memindai sheet bank yang tersedia di template..."):
    wb = load_template_readonly(TEMPLATE_PATH, TEMPLATE_MTIME)
    valid_sheets = list_valid_bank_sheets(TEMPLATE_PATH, TEMPLATE_MTIME)

if not valid_sheets:
    st.error("Tidak ada sheet yang terdeteksi sebagai laporan per-bank di template ini.")
    st.stop()

sheet_name = st.selectbox("Pilih bank yang mau di-update:", valid_sheets)
ws = wb[sheet_name]

header_row, header_hits = find_header_row(ws)
if header_row is None or header_hits == 0:
    st.error(
        "Tidak menemukan baris header periode (mis. 'Mar 24') di sheet ini. "
        "Coba pilih sheet lain, atau cek format template."
    )
    st.stop()

period_cols = get_period_columns(ws, header_row)
if not period_cols:
    st.error("Gagal mendeteksi kolom-kolom periode di sheet ini.")
    st.stop()

first_period_col = min(period_cols)
last_period_col = max(period_cols)


def period_fill_ratio(ws, col, header_row, sample=300):
    """Seberapa banyak baris di bawah header yang sudah terisi di kolom ini."""
    total, filled, count, r = 0, 0, 0, header_row + 1
    while r <= ws.max_row and count < sample:
        if ws.cell(r, col).value is not None:
            filled += 1
        total += 1
        count += 1
        r += 1
    return filled / total if total else 0


fill_ratios = {c: period_fill_ratio(ws, c, header_row) for c in period_cols}
# kolom periode terakhir yang SUDAH ada isinya (bukan cuma judulnya doang)
filled_period_cols = [c for c in period_cols if fill_ratios[c] > 0.05]
last_filled_col = max(filled_period_cols) if filled_period_cols else last_period_col

# Kasus umum di template ini: kolom periode terakhir sudah dibuat judulnya (mis. "Dec 25")
# tapi datanya masih kosong -> itu berarti kolom TUJUAN yang mau diisi, bukan kolom
# "periode sebelumnya" yang datanya jadi acuan pola/formula.
is_placeholder_col = (last_period_col != last_filled_col) and (fill_ratios[last_period_col] < 0.05)
style_source_col = last_filled_col  # kolom acuan pola format/formula ("periode sebelumnya")

if is_placeholder_col:
    target_col = last_period_col
    st.info(
        f"Kolom periode **'{ws.cell(header_row, last_period_col).value}'** "
        f"({get_column_letter(last_period_col)}) sudah ada di template tapi datanya masih "
        f"kosong -> sistem akan mengisi kolom itu langsung (bukan menambah kolom baru). "
        f"Pola/format diambil dari kolom sebelumnya, **"
        f"'{ws.cell(header_row, last_filled_col).value}'** ({get_column_letter(last_filled_col)})."
    )
else:
    target_col = last_period_col + 1
    st.success(
        f"Terdeteksi: baris header periode = baris {header_row}, "
        f"kolom periode terakhir yang sudah terisi = {get_column_letter(last_period_col)} "
        f"('{ws.cell(header_row, last_period_col).value}'). Sistem akan menambah kolom baru "
        f"setelahnya."
    )

# --- Deteksi format label periode dari header yang sudah ada (mis. 'Mar 23', 'Dec 25') ---
month_order, seen_months = [], set()
year_digit_len = 2
for c in period_cols:
    parsed = extract_month_year(ws.cell(header_row, c).value)
    if parsed:
        mon, yr = parsed
        if mon not in seen_months:
            seen_months.add(mon)
            month_order.append(mon)
        year_digit_len = len(yr)

if is_placeholder_col:
    # kolom tujuan sudah punya judul -> pakai itu sebagai default, tinggal dikonfirmasi
    existing_label = str(ws.cell(header_row, target_col).value).strip()
    st.markdown("**Konfirmasi periode yang mau diisi:**")
    new_period_label = st.text_input(
        "Judul kolom periode (sudah otomatis kebaca dari template, tinggal dikonfirmasi/ubah kalau perlu):",
        value=existing_label,
    )
else:
    last_parsed = extract_month_year(ws.cell(header_row, last_period_col).value)
    last_year_num = int(last_parsed[1]) if last_parsed else datetime.now().year % 100
    base_year_full = 2000 + last_year_num if (year_digit_len == 2 and last_year_num < 100) else last_year_num

    st.markdown("**Pilih periode baru yang mau ditambahkan sebagai kolom di template ini:**")
    pc1, pc2 = st.columns(2)
    with pc1:
        chosen_month = st.selectbox(
            "Kuartal (bulan akhir kuartal, ikut format yang sudah ada di template)",
            options=month_order if month_order else ["Mar", "Jun", "Sep", "Dec"],
        )
    with pc2:
        year_options = [base_year_full + d for d in (-1, 0, 1, 2)]
        chosen_year_full = st.selectbox(
            "Tahun",
            options=year_options,
            index=1,  # default: satu periode setelah yang terakhir di template
        )
    year_str = str(chosen_year_full)[-2:] if year_digit_len == 2 else str(chosen_year_full)
    new_period_label = f"{chosen_month} {year_str}"
    st.caption(
        f"Kolom baru akan diberi judul **'{new_period_label}'** "
        f"(mengikuti format periode yang sudah dipakai di template ini)."
    )

# Kumpulkan baris-baris akun di template (dari bawah header sampai baris kosong panjang),
# memakai kolom ACUAN (periode sebelumnya yang datanya sudah ada) untuk cek formula/nilai.
template_rows = []
empty_streak = 0
r = header_row + 1
while r <= ws.max_row and empty_streak < 15:
    label = row_label(ws, r, first_period_col)
    prev_val = ws.cell(r, style_source_col).value
    if label is None and prev_val is None:
        empty_streak += 1
    else:
        empty_streak = 0
        if label is not None:
            template_rows.append(
                {
                    "row": r,
                    "label": label,
                    "prev_value": prev_val,
                    "is_formula": isinstance(prev_val, str) and str(prev_val).startswith("="),
                }
            )
    r += 1

if not template_rows:
    st.error("Tidak ada baris akun terbaca di bawah header. Cek deteksi kolom label.")
    st.stop()


# ---------------------------------------------------------------------------------
# PARSE SOURCE (laporan keuangan baru) -> list of (label, [nilai1, nilai2, ...])
# Ditangkap SEMUA angka per baris (bukan cuma yang pertama) karena laporan bank
# sering punya beberapa kolom sekaligus per baris (mis. Individual 2025 | Individual
# 2024 | Konsolidasian 2025 | Konsolidasian 2024). User yang pilih kolom ke berapa
# yang mau dipakai (lihat "Pilih kolom nilai" di bawah).
# ---------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
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
                    values.append(float(v))
            if label and values:
                pairs.append((label, values))
    return pairs


def _clean_number(raw: str):
    c = str(raw).replace(".", "").replace(",", "").replace("(", "-").replace(")", "").strip()
    c = re.sub(r"[^\d\-]", "", c)
    if c in ("", "-"):
        return None
    try:
        return float(c)
    except ValueError:
        return None


def _pairs_from_table_rows(table):
    pairs = []
    for row in table:
        cells = [c for c in row if c is not None and str(c).strip() != ""]
        if len(cells) < 2:
            continue
        label = str(cells[0]).strip()
        if looks_like_period(label) or label == "":
            continue
        values = [v for v in (_clean_number(c) for c in cells[1:]) if v is not None]
        if values:
            pairs.append((label, values))
    return pairs


NUM_TOKEN = re.compile(r"\(?-?\d[\d.,]*\)?")


def _pairs_from_text_lines(text):
    """Fallback kalau ekstraksi tabel gagal/terlalu sedikit: baca per baris teks,
    ambil bagian sebelum angka pertama sebagai label, SEMUA angka di baris itu
    sebagai daftar nilai (posisi 1, 2, 3, dst dari kiri). Nomor urut di depan baris
    (mis. '1. Kas ...') dibuang dulu supaya tidak ketuker jadi dianggap angka nilai."""
    pairs = []
    for raw_line in text.split("\n"):
        line = strip_leading_enumerators(raw_line.strip())
        if not line or looks_like_period(line):
            continue
        nums = list(NUM_TOKEN.finditer(line))
        if not nums:
            continue
        label = line[: nums[0].start()].strip(" .:-")
        if len(label) < 2 or not re.search(r"[A-Za-z]", label):
            continue
        values = [v for v in (_clean_number(n.group()) for n in nums) if v is not None]
        if values:
            pairs.append((label, values))
    return pairs


@st.cache_data(show_spinner=False)
def parse_source_pdf(file_bytes):
    pairs = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Strategi 1: deteksi tabel standar (ada garis pemisah)
            for table in page.extract_tables():
                pairs.extend(_pairs_from_table_rows(table))
            # Strategi 2: deteksi tabel tanpa garis (murni berdasarkan posisi teks)
            try:
                for table in page.extract_tables(
                    {"vertical_strategy": "text", "horizontal_strategy": "text"}
                ):
                    pairs.extend(_pairs_from_table_rows(table))
            except Exception:
                pass
            # Strategi 3 (fallback): baca per baris teks biasa
            text = page.extract_text() or ""
            pairs.extend(_pairs_from_text_lines(text))

    # Buang duplikat persis (label+nilai-nilai sama) yang muncul dari beberapa strategi
    seen, unique_pairs = set(), []
    for label, values in pairs:
        key = (label.strip().lower(), tuple(values))
        if key not in seen:
            seen.add(key)
            unique_pairs.append((label, values))
    return unique_pairs


src_bytes = source_file.getvalue()
with st.spinner(f"Membaca '{source_file.name}'..."):
    if source_file.name.lower().endswith(".pdf"):
        if not HAS_PDF:
            st.error("pdfplumber belum terinstall. Jalankan: pip install pdfplumber")
            st.stop()
        raw_source_rows = parse_source_pdf(src_bytes)
    else:
        raw_source_rows = parse_source_excel(src_bytes)

if not raw_source_rows:
    st.error("Tidak ada data (label + angka) yang berhasil diekstrak dari laporan baru.")
    st.stop()

st.success(f"✅ File '{source_file.name}' berhasil dibaca — {len(raw_source_rows)} baris akun terdeteksi.")

max_value_cols = max(len(v) for _, v in raw_source_rows)
st.markdown("**Pilih kolom nilai yang mau dipakai** (kalau satu baris di laporan punya beberapa angka sekaligus, mis. Individual/Konsolidasian x tahun ini/lalu):")
value_col_idx = st.selectbox(
    "Ambil angka ke berapa dari kiri, di tiap baris?",
    options=list(range(1, max_value_cols + 1)),
    index=0,
    format_func=lambda i: f"Angka ke-{i}",
)

with st.expander("🔍 Lihat detail akun & semua angka yang berhasil dibaca dari file", expanded=False):
    st.caption(
        "Kolom yang di-highlight (dipilih di atas) itu yang akan dipakai sebagai nilai. "
        "Kalau labelnya berantakan atau angkanya di kolom yang salah, berarti sumber masalah "
        "ada di ekstraksi file, bukan di proses matching."
    )
    preview_debug = pd.DataFrame(
        [
            {"Akun (Laporan Baru)": lbl, **{f"Angka ke-{i+1}": (v[i] if i < len(v) else None) for i in range(max_value_cols)}}
            for lbl, v in raw_source_rows[:200]
        ]
    )
    st.dataframe(preview_debug, use_container_width=True, height=300)

source_pairs = [(lbl, v[value_col_idx - 1]) for lbl, v in raw_source_rows if len(v) >= value_col_idx]


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


apply_clicked = st.button(f"🚀 Generate Laporan — Tambah Kolom '{new_period_label}'", type="primary")

if apply_clicked:
    with st.spinner("Menulis kolom baru ke template... (tidak lama)"):
        # Buat salinan workbook yang FRESH khusus untuk ditulisi — bukan objek
        # yang di-cache (load_template_readonly), supaya tidak ada perubahan yang
        # "nempel" ke cache bersama dan bocor ke user/sesi lain.
        fresh_bytes = read_template_bytes(TEMPLATE_PATH, TEMPLATE_MTIME)
        wb_out = openpyxl.load_workbook(io.BytesIO(fresh_bytes), data_only=False)
        ws_out = wb_out[sheet_name]

        new_col = target_col

        if not is_placeholder_col:
            ws_out.column_dimensions[get_column_letter(new_col)].width = ws_out.column_dimensions[
                get_column_letter(style_source_col)
            ].width

        header_dst = ws_out.cell(header_row, new_col)
        header_dst.value = new_period_label.strip()
        if not is_placeholder_col:
            copy_cell_style(ws_out.cell(header_row, style_source_col), header_dst)

        edited_lookup = {row["Baris Template"]: row for row in edited_df.to_dict("records")}

        applied, skipped = 0, 0
        for tr in template_rows:
            row_num = tr["row"]
            src_cell = ws_out.cell(row_num, style_source_col)
            dst_cell = ws_out.cell(row_num, new_col)
            if not is_placeholder_col:
                copy_cell_style(src_cell, dst_cell)

            info = edited_lookup.get(row_num)

            if tr["is_formula"]:
                dst_cell.value = shift_formula(str(tr["prev_value"]), style_source_col, new_col, row_num)
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

    st.subheader(f"📄 Preview hasil kompilasi — kolom '{new_period_label}'")
    preview_rows = []
    for tr in template_rows:
        val = ws_out.cell(tr["row"], new_col).value
        preview_rows.append(
            {
                "Baris": tr["row"],
                "Akun": tr["label"],
                "Tipe": "Formula" if tr["is_formula"] else "Nilai",
                f"{new_period_label}": val,
            }
        )
    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, height=350)

    out = io.BytesIO()
    wb_out.save(out)
    out.seek(0)

    fname = f"{sheet_name}_updated_{datetime.now().strftime('%Y%m%d')}.xlsx"
    st.download_button(
        "⬇️ Download template hasil update (.xlsx)",
        data=out,
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )