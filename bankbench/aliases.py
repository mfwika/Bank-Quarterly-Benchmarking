"""Kamus padanan nama akun: label di TEMPLATE -> label di LAPORAN PUBLIKASI.

Dua sumber:
1. SEED_ALIASES (di bawah) — padanan bawaan format publikasi OJK terbaru vs
   label lama di template.
2. mappings.json — padanan yang "dipelajari" dari koreksi manual user di
   aplikasi (tombol 'Simpan pemetaan'). Commit file ini ke repo supaya
   tersimpan permanen.

Kunci: '<label template bersih>' atau '<label template bersih> | <induk bersih>'
(pakai induk kalau labelnya kembar, mis. 'Kredit' di bawah 'Cadangan kerugian').
"""
import json
import os

from .text import clean_label

MAPPINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mappings.json")

SEED_ALIASES = {
    "BS": {
        "surat berharga": ["surat berharga yang dimiliki"],
        "tagihan spot dan derivatif": ["tagihan spot dan derivatif forward", "tagihan derivatif"],
        "pinjaman yang diberikan dan piutang | kredit": ["kredit yang diberikan", "kredit"],
        "penyertaan": ["penyertaan modal"],
        "surat berharga | cadangan kerugian penurunan nilai aset keuangan": ["surat berharga yang dimiliki"],
        "kredit | cadangan kerugian penurunan nilai aset keuangan": [
            "kredit yang diberikan dan pembiayaan syariah", "kredit yang diberikan", "kredit"],
        "lainnya | cadangan kerugian penurunan nilai aset keuangan": ["lainnya", "aset keuangan lainnya"],
        "simpanan berjangka": ["deposito"],
        "pinjaman dari bank indonesia": ["liabilitas kepada bank indonesia"],
        "pinjaman dari bank lain": ["liabilitas kepada bank lain"],
        "liabilitas spot dan derivatif": ["liabilitas spot dan derivatif forward"],
        "utang surat berharga yang dijual dengan janji dibeli kembali repo": [
            "liabilitas atas surat berharga yang dijual dengan janji dibeli kembali repo"],
        "utang akseptasi": ["liabilitas akseptasi"],
        "pinjaman yang diterima lainnya | pinjaman yang diterima": [
            "pinjaman pembiayaan yang diterima", "pinjaman yang diterima"],
        "pendapatan kerugian komprehensif lainnya": ["penghasilan komprehensif lain", "pendapatan komprehensif lain"],
        "tahun tahun lalu | laba rugi": ["tahun tahun lalu", "saldo laba tahun tahun lalu"],
        "tahun berjalan | laba rugi": ["tahun berjalan", "laba tahun berjalan"],
        "kepentingan non pengendali": ["kepentingan non pengendali", "kepentingan minoritas"],
        "total aset": ["total aset", "jumlah aset"],
        "total liabilitas": ["total liabilitas", "jumlah liabilitas"],
        "total ekuitas": ["total ekuitas", "jumlah ekuitas"],
        "jumlah kewajiban dan modal": ["total liabilitas dan ekuitas", "jumlah liabilitas dan ekuitas"],
    },
    "IS": {
        "peningkatan nilai wajar aset keuangan mark to market": [
            "keuntungan kerugian dari peningkatan penurunan nilai wajar aset keuangan"],
        "penurunan nilai wajar kewajiban keuangan mark to market": [
            "keuntungan kerugian dari penurunan peningkatan nilai wajar liabilitas keuangan"],
        "keuntungan penjualan aset keuangan": ["keuntungan kerugian dari penjualan aset keuangan"],
        "keuntungan transaksi spot dan derivatif realised": [
            "keuntungan kerugian dari transaksi spot dan derivatif forward realised"],
        "keuntungan dari penyertaan dengan equity method": [
            "keuntungan kerugian dari penyertaan dengan equity method"],
        "deviden": ["pendapatan dividen", "dividen"],
        "komisi provisi fee dan administrasi | pendapatan operasional selain bunga": [
            "pendapatan komisi provisi fee dan administrasi"],
        "pendapatan lainnya": ["pendapatan lainnya"],
        "pendapatan bunga bersih": ["pendapatan beban bunga bersih"],
        "laba operasional": ["laba rugi operasional"],
        "keuntungan kerugian penjabaran transaksi valuta asing": [
            "keuntungan kerugian dari penjabaran transaksi valuta asing"],
        "taksiran pajak periode berjalan": ["taksiran pajak tahun berjalan", "taksiran pajak periode berjalan"],
        "keuntungan kerugian aktuarial program manfaat pasti": [
            "pengukuran kembali atas program imbalan pasti", "pengukuran kembali atas program manfaat pasti"],
        "penyesuaian akibat penjabaran laporan keuangan dlm mata uang asing": [
            "selisih kurs penjabaran laporan keuangan dalam mata uang asing"],
        "total laba komprehensif tahun berjalan": ["total penghasilan komprehensif tahun berjalan",
                                                   "total laba komprehensif periode berjalan"],
    },
    "CAP": {
        "modal disetor": ["modal disetor setelah dikurangi treasury stock", "modal disetor"],
        "cadangan tambahan modal disclosed reserve": ["cadangan tambahan modal"],
        "level atas upper tier 2": ["modal pelengkap tier 2", "modal pelengkap"],
        "aset tertimbang menurut risiko atmr untuk risiko kredit": ["atmr risiko kredit"],
        "aset tertimbang menurut risiko atmr untuk risiko operasional": ["atmr risiko operasional"],
        "aset tertimbang menurut risiko atmr untuk risiko pasar": ["atmr risiko pasar"],
        "modal inti": ["modal inti tier 1"],
        "total modal inti dan modal pelengkap a b c": ["total modal"],
    },
}


def alias_key(label, parent=None) -> str:
    k = clean_label(label)
    return f"{k} | {clean_label(parent)}" if parent else k


def load_learned(path=MAPPINGS_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_learned(data: dict, path=MAPPINGS_PATH):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)


def merged_aliases(learned: dict | None = None) -> dict:
    out = {sec: {k: [clean_label(x) for x in v] for k, v in d.items()} for sec, d in SEED_ALIASES.items()}
    for sec, d in (learned or {}).items():
        for k, v in d.items():
            bucket = out.setdefault(sec, {}).setdefault(k, [])
            for x in v:
                cx = clean_label(x)
                if cx not in bucket:
                    bucket.insert(0, cx)  # hasil belajar diprioritaskan
    return out


def lookup(aliases: dict, section: str, label, parent=None) -> list:
    d = aliases.get(section, {})
    out = []
    if parent:
        out += d.get(alias_key(label, parent), [])
    out += d.get(alias_key(label), [])
    return out


def add_learned(learned: dict, section: str, label, parent, source_label) -> dict:
    key = alias_key(label, parent)
    bucket = learned.setdefault(section, {}).setdefault(key, [])
    cs = clean_label(source_label)
    if cs and cs not in bucket:
        bucket.append(cs)
    return learned
