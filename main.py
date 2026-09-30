"""Auto-Update Template Benchmarking Bank — MODE STRICT (ikut pola periode acuan).

Alur:
1. Template (template.xlsx) tersimpan di repo / backend.
2. User upload laporan keuangan publikasi (PDF / Excel) — boleh beberapa bank &
   beberapa periode sekaligus.
3. Per file: tebak bank (sheet) & periode. Angka diisi dengan MENIRU POLA periode acuan:
     - Neraca                                  -> pola Desember tahun lalu
     - Laba Rugi, KPMM, Rasio & NPL            -> pola periode yang sama tahun lalu
   Pola = akun laporan (atau jumlah beberapa akun) yang angka pembandingnya persis sama
   dengan isi template di periode acuan. Tidak ada pola -> dikosongkan & ditandai.
4. File untuk bank yang sama diproses berurutan (lama -> baru), jadi hasil Dec 25 langsung
   jadi acuan untuk Jun 26.
5. Review -> cek total -> generate & download.
"""
import hashlib
import io
import json
import os
import warnings
from datetime import datetime

import openpyxl
import pandas as pd
import streamlit as st
from openpyxl.utils import get_column_letter


def _reload_changed_bankbench():
    """Streamlit (juga di Cloud) hanya me-reload main.py saat repo di-update; modul bankbench
    yang sudah ter-import tetap versi lama -> ImportError. Reload kalau file-nya berubah."""
    import importlib
    import sys

    order = ["text", "periods", "aliases", "template_model", "source_parser", "matcher", "pattern",
             "writer", "banks"]
    stamps = sys.__dict__.setdefault("_bankbench_mtimes", {})
    mods = [sys.modules.get(f"bankbench.{n}") for n in order]
    changed = False
    for mod in mods:
        f = getattr(mod, "__file__", None)
        if f and os.path.exists(f):
            mt = os.path.getmtime(f)
            changed |= stamps.get(f, mt) != mt
            stamps[f] = mt
    if changed:
        for mod in mods:
            if mod is not None:
                importlib.reload(mod)


_reload_changed_bankbench()

from bankbench.aliases import MAPPINGS_PATH, add_learned, load_learned, merged_aliases, save_learned
from bankbench.banks import detect_bank, sheet_display
from bankbench.matcher import reconcile
from bankbench.pattern import FALLBACK_METHODS, StrictMatcher, reference_period
from bankbench.periods import EN_ABBR, detect_report_period, format_period_label
from bankbench.source_parser import ocr_available, parse_source
from bankbench.template_model import SECTION_NAMES, load_bank_models
from bankbench.writer import apply_to_workbook

st.set_page_config(page_title="Auto-Update Template Benchmarking", layout="wide")
st.title("Auto-Update Template Benchmarking")
st.caption(
    "Upload laporan keuangan publikasi bank → sistem mengisi template dengan **meniru pola periode acuan** "
    "(Neraca: Desember tahun lalu · Laba Rugi / KPMM / Rasio / NPL: periode yang sama tahun lalu)."
)

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.xlsx")
if not os.path.exists(TEMPLATE_PATH):
    st.error(
        "File template belum ada. Taruh file Excel template dengan nama persis **template.xlsx** "
        "di folder yang sama dengan main.py (di repo), lalu commit."
    )
    st.stop()
TEMPLATE_MTIME = os.path.getmtime(TEMPLATE_PATH)

QUARTER_MONTHS = [3, 6, 9, 12]
QUARTER_NAMES = {3: "Q1 (Mar)", 6: "Q2 (Jun)", 9: "Q3 (Sep)", 12: "Q4 (Dec)"}
SOURCE_NONE = "(kosong / tidak diisi)"
ALL_SECTIONS = ["BS", "IS", "CAP", "RATIO", "NPL"]


# ---------------------------------------------------------------------------------
# cache
# ---------------------------------------------------------------------------------
# Naikkan angka ini setiap struktur data parser/model berubah -> cache lama otomatis dibuang
# (Streamlit Cloud tidak selalu restart penuh setelah update kode).
CACHE_VERSION = 4


@st.cache_data(show_spinner=False)
def get_models(path, mtime, version=CACHE_VERSION):
    return load_bank_models(path)


@st.cache_data(show_spinner=False)
def get_template_bytes(path, mtime):
    with open(path, "rb") as fh:
        return fh.read()


@st.cache_data(show_spinner=False, max_entries=30)
def parse_cached(name, data, version=CACHE_VERSION):
    return parse_source(name, data)


@st.cache_data(show_spinner=False, max_entries=60)
def detect_bank_cached(fk, _text, _rows, _models, _aliases, version=CACHE_VERSION):
    return detect_bank(_text, _rows, _models, _aliases)


def file_key(f):
    return hashlib.md5(f.getvalue()).hexdigest()[:10]


def fmt_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if abs(v) < 1000 and v != int(v):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{v:,.0f}".replace(",", ".")


def plabel(p):
    return f"{EN_ABBR[p[0]]} {str(p[1])[-2:]}"


with st.spinner("Membaca struktur template (sekali saja, lalu di-cache)..."):
    models = get_models(TEMPLATE_PATH, TEMPLATE_MTIME, CACHE_VERSION)
if not models:
    st.error("Tidak ada sheet bank (berisi NERACA / LABA RUGI / CAPITAL ADEQUACY) yang terdeteksi di template.")
    st.stop()

if "learned" not in st.session_state:
    st.session_state.learned = load_learned()
aliases = merged_aliases(st.session_state.learned)

with st.sidebar:
    st.header("ℹ️ Cara kerja (mode strict)")
    st.markdown(
        "**Periode acuan pola**\n"
        "- Neraca → **Desember** tahun lalu\n"
        "- Laba Rugi, KPMM, Rasio, NPL → **periode yang sama tahun lalu**\n\n"
        "**Cara mengisi**\n"
        "1. Ambil nilai template di periode acuan.\n"
        "2. Cari akun laporan (atau jumlah 2–4 akun) yang angka *pembanding*-nya persis sama.\n"
        "3. Pakai resep yang sama untuk angka periode berjalan.\n"
        "4. Pola tidak ada (mis. kolom Desember belum terisi, angka di-restate) → akun tetap **dikenali**: "
        "memori pola bank ini → nama akun/kamus padanan (+ kebiasaan penjumlahan yang dipelajari) → "
        "penyeimbang total Neraca. Hasilnya ditandai 🟡 **CEK**.\n"
        "5. Akun yang biasanya kosong / tidak dikenali → dikosongkan & ditandai ⚠.\n\n"
        "**Entitas**: Neraca/Laba Rugi/KPMM → Konsolidasian (kecuali judul seksi template 'Bank only'). "
        "Rasio & NPL → ikut kolom yang cocok di periode acuan.\n\n"
        "**Beberapa periode sekaligus**: file bank yang sama diproses dari periode lama ke baru, "
        "jadi hasil Dec 25 langsung jadi acuan Jun 26."
    )
    st.divider()
    st.caption(f"Template: `template.xlsx` — {len(models)} sheet bank terdeteksi.")

# ---------------------------------------------------------------------------------
# STEP 1: upload
# ---------------------------------------------------------------------------------
uploads = st.file_uploader(
    "① Drag & drop laporan keuangan publikasi (PDF / Excel) — boleh beberapa bank & periode sekaligus",
    type=["pdf", "xlsx", "xlsm"],
    accept_multiple_files=True,
)
if not uploads:
    st.info("Upload minimal satu laporan publikasi untuk mulai.")
    st.stop()

parsed = {}
for f in uploads:
    with st.spinner(f"Membaca '{f.name}'... (PDF berupa gambar dibaca pakai OCR, bisa ±1 menit)"):
        try:
            rows, text = parse_cached(f.name, f.getvalue(), CACHE_VERSION)
        except Exception as e:  # file rusak / terenkripsi / bukan PDF teks
            st.error(f"Gagal membaca '{f.name}': {e}")
            continue
    if not [r for r in rows if r.section in ("BS", "IS", "CAP", "?")]:
        st.error(
            f"Tidak ada akun + angka yang terbaca dari '{f.name}'. Kalau PDF-nya berupa gambar/scan, "
            + ("OCR sudah dicoba tapi gagal — " if ocr_available() else "OCR (Tesseract) belum terpasang di server — ")
            + "pakai versi PDF teks / Excel dari website bank / OJK."
        )
        continue
    parsed[file_key(f)] = (f, rows, text)
if not parsed:
    st.stop()

sheet_names = list(models)

# ---------------------------------------------------------------------------------
# STEP 2: tentukan bank & periode tiap file (nilai widget dari run sebelumnya)
# ---------------------------------------------------------------------------------
cfg = {}
for fk, (f, rows, text) in parsed.items():
    ranking = detect_bank_cached(fk, text, rows, models, aliases)
    auto_sheet = ranking[0][0]
    det = detect_report_period(text)
    if not det:
        lp = models[auto_sheet].latest_period() or (12, datetime.now().year - 1)
        det = (lp[0] + 3, lp[1]) if lp[0] < 12 else (3, lp[1] + 1)
    sheet = st.session_state.get(f"sheet_{fk}", auto_sheet)
    month = st.session_state.get(f"month_{fk}", det[0])
    year = int(st.session_state.get(f"year_{fk}", det[1]))
    cfg[fk] = dict(sheet=sheet, month=month, year=year, auto_sheet=auto_sheet, ranking=ranking, detected=det)

# urutan proses: per bank, periode lama -> baru (hasil periode lama jadi acuan periode baru)
order = sorted(cfg, key=lambda k: (cfg[k]["sheet"], cfg[k]["year"], cfg[k]["month"]))
work_models = {}


def build_df(results, option_of):
    recs = []
    for r in results:
        src_opt = option_of.get(r.source_idx, SOURCE_NONE) if r.source_idx is not None else SOURCE_NONE
        recs.append({
            "Baris": r.row,
            "Seksi": r.section,
            "Akun (Template)": ("   ↳ " if r.parent else "") + r.label,
            "Tipe": r.kind,
            "Akun di Laporan": src_opt if r.method != "Saran nama akun" else SOURCE_NONE,
            "Nilai": r.value,
            "Rumus": r.formula or "",
            "Periode lalu": r.prev_value,
            "Metode": r.method,
            "Catatan": r.note if r.method != "Saran nama akun" else f"{r.note} (saran: {r.source_label})",
        })
    return pd.DataFrame(recs).set_index("Baris", drop=False)


def on_editor_change(state_key, editor_key, shown_index, matcher_key):
    """Terapkan editan ke tabel utama. Ganti 'Akun di Laporan' -> nilai ikut diambil
    dari akun yang dipilih (periode berjalan, entitas yang sama)."""
    df = st.session_state[state_key]
    ctx = st.session_state[matcher_key]
    edits = st.session_state.get(editor_key, {}).get("edited_rows", {})
    for pos, changes in edits.items():
        row_id = shown_index[int(pos)]
        for col, val in changes.items():
            if col == "Akun di Laporan":
                df.at[row_id, col] = val
                sr = ctx["src_by_option"].get(val)
                tr = ctx["rows_by_num"].get(row_id)
                if sr is None or tr is None:
                    df.at[row_id, "Nilai"] = None
                else:
                    v, _ = ctx["matcher"].value_for(tr, sr)
                    df.at[row_id, "Nilai"] = v
                    add_learned(st.session_state.learned, tr.section, tr.label, tr.parent, sr.label)
                df.at[row_id, "Rumus"] = ""
                df.at[row_id, "Metode"] = "Manual"
            elif col in ("Nilai", "Rumus"):
                df.at[row_id, col] = val
                if col == "Nilai":
                    df.at[row_id, "Rumus"] = ""
                df.at[row_id, "Metode"] = "Manual"
    st.session_state[state_key] = df
    st.session_state.pop(editor_key, None)


def final_values(df):
    """row -> angka atau rumus (string '=...') yang akan ditulis."""
    out = {}
    for r, row in df.iterrows():
        if row["Tipe"] == "Formula":
            continue
        if isinstance(row["Rumus"], str) and row["Rumus"].startswith("="):
            out[int(r)] = row["Rumus"]
        elif row["Nilai"] is not None and not pd.isna(row["Nilai"]):
            out[int(r)] = float(row["Nilai"])
    return out


# ---------------------------------------------------------------------------------
# STEP 3: proses berurutan (tanpa tampilan) -> simpan hasil
# ---------------------------------------------------------------------------------
jobs = {}
chain_sig = {}
for fk in order:
    f, rows, text = parsed[fk]
    c = cfg[fk]
    base = work_models.get(c["sheet"], models[c["sheet"]])
    target_col, exists = base.target_col_for(c["month"], c["year"])
    label = base.period_cols.get(target_col) or format_period_label(
        c["month"], c["year"], like=base.period_cols[base.last_period_col()])
    memory = st.session_state.learned.get("_recipes", {}).get(c["sheet"], {})
    conventions = st.session_state.learned.get("_conventions", {})
    matcher = StrictMatcher(base, rows, target_col, aliases, (c["month"], c["year"]),
                            recipe_hints={int(k): v for k, v in memory.items()}, conventions=conventions)
    results = matcher.run()
    source_rows = matcher.source_all
    option_of = {r.idx: f"#{r.idx} · {r.label[:70]} [{fmt_num(matcher.cur_value(r))}]" for r in source_rows
                 if r.values}
    src_by_option = {opt: next(s for s in source_rows if s.idx == i) for i, opt in option_of.items()}
    # hasil laporan periode sebelumnya (bank yang sama) ikut menentukan pola -> ikut di signature
    sig = (fk, c["sheet"], target_col, c["year"], c["month"], chain_sig.get(c["sheet"], ""))
    state_key, matcher_key = f"df_{fk}", f"matcher_{fk}"
    if st.session_state.get(f"sig_{fk}") != sig:
        st.session_state[state_key] = build_df(results, option_of)
        st.session_state[f"sig_{fk}"] = sig
        st.session_state.pop(f"editor_{fk}", None)
    st.session_state[matcher_key] = {
        "matcher": matcher, "src_by_option": src_by_option,
        "rows_by_num": {r.row: r for r in base.rows + (getattr(base, "extra_rows", None) or [])},
    }
    df = st.session_state[state_key]
    values = final_values(df)
    learned_recipes = matcher.recipe_memory()
    work_models[c["sheet"]] = base.with_column(target_col, label, values, hints=learned_recipes)
    if learned_recipes:  # memori resep ikut disimpan di mappings.json (belajar antar-sesi)
        mem = st.session_state.learned.setdefault("_recipes", {}).setdefault(c["sheet"], {})
        mem.update({str(k): v for k, v in learned_recipes.items()})
    for sec, conv in matcher.learned_conventions().items():  # kebiasaan penjumlahan lintas bank
        dst = st.session_state.learned.setdefault("_conventions", {}).setdefault(sec, {})
        for k, v in conv.items():
            dst[k] = sorted(set(dst.get(k, [])) | set(v))
    chain_sig[c["sheet"]] = hashlib.md5(json.dumps(sorted(values.items()), default=str).encode()).hexdigest()[:8]
    jobs[fk] = dict(file=f.name, sheet=c["sheet"], model=base, target_col=target_col, exists=exists, label=label,
                    month=c["month"], year=c["year"], values=values, matcher=matcher, option_of=option_of)

# ---------------------------------------------------------------------------------
# STEP 4: tampilan per file
# ---------------------------------------------------------------------------------
st.subheader("② Review per laporan")
tabs = st.tabs([f"{parsed[fk][0].name} → {jobs[fk]['sheet']} {jobs[fk]['label']}" for fk in order])
for tab, fk in zip(tabs, order):
    f, rows, text = parsed[fk]
    c, job = cfg[fk], jobs[fk]
    model, matcher, target_col = job["model"], job["matcher"], job["target_col"]
    with tab:
        a1, a2, a3 = st.columns([2, 1, 1])
        with a1:
            st.selectbox("Bank / sheet tujuan", sheet_names, index=sheet_names.index(c["sheet"]),
                         format_func=lambda n: sheet_display(models[n]), key=f"sheet_{fk}")
            reason = {n: r for n, _, r in c["ranking"]}
            st.caption(f"Tebakan otomatis: **{c['auto_sheet']}** — {reason[c['auto_sheet']]}")
        with a2:
            st.selectbox("Kuartal", QUARTER_MONTHS, index=QUARTER_MONTHS.index(c["month"]),
                         format_func=lambda m: QUARTER_NAMES[m], key=f"month_{fk}")
        with a3:
            st.number_input("Tahun", min_value=2000, max_value=2100, value=c["year"], step=1, key=f"year_{fk}")
            st.caption(f"Terdeteksi dari laporan: {c['detected'][0]:02d}/{c['detected'][1]}")

        col_letter = get_column_letter(target_col)
        if job["exists"] and model.fill_ratio(target_col) > 0.05:
            st.warning(f"Kolom **{job['label']}** (kolom {col_letter}) SUDAH BERISI data → angka lama akan ditimpa.")
        elif job["exists"]:
            st.info(f"Kolom **{job['label']}** sudah ada (kolom {col_letter}) → akan diisi.")
        else:
            st.success(f"Kolom baru **{job['label']}** akan ditambahkan di kolom {col_letter}.")

        # periode acuan per seksi
        ref_info = []
        for sec in ("BS", "IS", "CAP", "RATIO"):
            per = reference_period("BS" if sec == "BS" else "IS", c["month"], c["year"])
            col = model.find_period_col(*per)
            filled = col is not None and model.fill_ratio(col) > 0.05
            name = SECTION_NAMES[sec].split(" /")[0].split(" (")[0]
            ent = matcher.entity.get(sec, "ikut pola")
            ref_info.append(f"{name}: **{plabel(per)}**" + ("" if filled else " ⚠ belum terisi di template")
                            + (f" · {'Konsolidasian' if ent == 'KONS' else 'Individual' if ent == 'IND' else ent}"))
        st.markdown("🔎 **Periode acuan pola** — " + " · ".join(ref_info))
        missing = [s for s in ("BS", "IS", "CAP") if not matcher.ref_cols.get(s)
                   or model.fill_ratio(matcher.ref_cols[s]) <= 0.05]
        if missing:
            per = reference_period(missing[0], c["month"], c["year"])
            st.info(f"Periode acuan **{plabel(per)}** belum terisi di template sheet ini → seksi "
                    f"{', '.join(missing)} diisi dari **pengenalan nama akun + memori pola** (ditandai 🟡 CEK) dan "
                    "dicek ke total laporan. Kalau mau strict penuh, upload juga laporan periode "
                    f"{plabel(per)} (akan diproses lebih dulu).")
        if any(getattr(r, "ocr", False) for r in rows):
            st.warning("📷 Tabel di file ini berupa **gambar**, dibaca dengan OCR. Angka hasil OCR bisa salah baca "
                       "— cek tabel 'Cek total'.")

        df = st.session_state[f"df_{fk}"]
        is_val = df["Tipe"] == "Nilai"
        filled = df["Nilai"].notna() | (df["Rumus"].astype(str).str.startswith("="))
        n_pola = int(df["Metode"].isin(["Pola angka", "Pola penjumlahan", "Rumus acuan"]).sum())
        n_fb = int(df["Metode"].isin(FALLBACK_METHODS).sum())
        n_miss = int((is_val & ~filled).sum())
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Baris yang perlu diisi", int(is_val.sum()))
        m2.metric("Terisi sesuai pola", n_pola)
        m3.metric("🟡 Dikenali dari nama/memori", n_fb)
        m4.metric("⚠ Kosong", n_miss)
        m5.metric("Diisi manual", int((df["Metode"] == "Manual").sum()))

        fc1, fc2 = st.columns([3, 2])
        with fc1:
            secs = st.multiselect("Seksi", ALL_SECTIONS, default=ALL_SECTIONS,
                                  format_func=lambda s: SECTION_NAMES[s], key=f"secs_{fk}")
        with fc2:
            view = st.radio("Tampilkan", ["Baris yang diisi", "⚠ Perlu dicek saja", "Semua baris"],
                            horizontal=True, key=f"view_{fk}")
        shown = df[df["Seksi"].isin(secs)]
        if view == "Baris yang diisi":
            shown = shown[(shown["Tipe"] == "Nilai") | shown["Nilai"].notna()]
        elif view.startswith("⚠"):
            f2 = shown["Nilai"].notna() | shown["Rumus"].astype(str).str.startswith("=")
            shown = shown[(shown["Tipe"] == "Nilai") & (~f2 | shown["Catatan"].str.contains("⚠|CEK", na=False))]

        st.data_editor(
            shown,
            key=f"editor_{fk}",
            on_change=on_editor_change,
            args=(f"df_{fk}", f"editor_{fk}", list(shown.index), f"matcher_{fk}"),
            width="stretch",
            height=460,
            hide_index=True,
            disabled=["Baris", "Seksi", "Akun (Template)", "Tipe", "Periode lalu", "Metode", "Catatan"],
            column_config={
                "Baris": st.column_config.NumberColumn(width="small"),
                "Akun di Laporan": st.column_config.SelectboxColumn(
                    options=[SOURCE_NONE] + list(job["option_of"].values()), width="large"),
                "Nilai": st.column_config.NumberColumn(format="%.2f"),
                "Rumus": st.column_config.TextColumn(help="Kalau diisi (mis. NPL = (a+b+c)/1000), rumus ini yang ditulis"),
                "Periode lalu": st.column_config.NumberColumn(format="%.2f"),
            },
        )
        st.caption("🟡 CEK = pola angka tidak ada, akun dikenali dari nama/memori — mohon dicek. "
                   "⚠ = tidak dikenali → dikosongkan. Kalau yakin, pilih **Akun di Laporan** "
                   "atau ketik **Nilai** secara manual. Baris 'Formula' dihitung otomatis oleh Excel.")

        numeric = {int(r): float(v) for r, v in df["Nilai"].items()
                   if v is not None and not pd.isna(v) and df.at[r, "Tipe"] != "Formula"}
        checks = reconcile(matcher, numeric)
        if checks:
            chk = pd.DataFrame(checks)
            bad = int((chk["Status"] == "BEDA").sum())
            with st.expander(f"✅ Cek total vs laporan — {len(chk) - bad} cocok, {bad} beda", expanded=bad > 0):
                show = chk.copy()
                for col in ("Hasil hitung", "Di laporan", "Selisih"):
                    show[col] = show[col].map(fmt_num)
                st.dataframe(show, width="stretch", hide_index=True)
                st.caption("Total dihitung dari formula template memakai angka yang akan diisi, lalu dibandingkan dengan "
                           "total di laporan. 'BEDA' biasanya karena akun yang kosong di periode acuan (akun baru), "
                           "angka di-restate, atau beda klasifikasi — lihat Keterangan.")

# ---------------------------------------------------------------------------------
# STEP 5: generate
# ---------------------------------------------------------------------------------
st.subheader("③ Generate template")
annotate = st.checkbox("Beri comment di sel yang diisi manual / hasil penjumlahan / 🟡 CEK (biar gampang dicek di Excel)",
                       value=True)
if st.button(f"🚀 Update template — {len(jobs)} laporan", type="primary"):
    with st.spinner("Memuat template lengkap & menulis kolom... (±30–60 detik untuk file besar)"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wb = openpyxl.load_workbook(io.BytesIO(get_template_bytes(TEMPLATE_PATH, TEMPLATE_MTIME)))
        summary = []
        for fk in order:
            job = jobs[fk]
            df = st.session_state[f"df_{fk}"]
            notes = {}
            if annotate:
                for r, row in df.iterrows():
                    if int(r) in job["values"] and row["Metode"] in ("Manual", "Pola penjumlahan", *FALLBACK_METHODS):
                        notes[int(r)] = f"Auto-update ({row['Metode']}): {row['Catatan'] or row['Akun di Laporan']}"
            n = apply_to_workbook(wb, job["model"], job["target_col"], job["label"], job["month"], job["year"],
                                  job["values"], notes or None)
            summary.append({"File": job["file"], "Sheet": job["sheet"], "Periode": job["label"],
                            "Kolom": get_column_letter(job["target_col"]), "Sel terisi": n})
        out = io.BytesIO()
        wb.save(out)
    st.session_state["output"] = (out.getvalue(), f"template_update_{datetime.now():%Y%m%d_%H%M}.xlsx", summary)

if "output" in st.session_state:
    data, fname, summary = st.session_state["output"]
    st.dataframe(pd.DataFrame(summary), hide_index=True, width="stretch")
    st.download_button("⬇️ Download template hasil update (.xlsx)", data=data, file_name=fname,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption("Catatan: openpyxl tidak menyimpan ulang chart/gambar yang ada di workbook.")

if st.session_state.learned:
    with st.expander("🧠 Memori pola (pasangan manual + resep penjumlahan per bank)"):
        st.json(st.session_state.learned, expanded=False)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 Simpan ke mappings.json (server)"):
                save_learned(st.session_state.learned)
                st.success(f"Tersimpan di {MAPPINGS_PATH}. Di Streamlit Cloud file ini hilang saat app restart — "
                           "download lalu commit ke repo supaya permanen.")
        with b2:
            st.download_button("⬇️ Download mappings.json",
                               data=json.dumps(st.session_state.learned, indent=2, ensure_ascii=False),
                               file_name="mappings.json", mime="application/json")
