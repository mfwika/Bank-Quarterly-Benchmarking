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


# Laporan publikasi versi bahasa Inggris (mis. SMBC Indonesia, bank asing)
ENGLISH_ALIASES = {
    "BS": {
        "kas": ["cash"],
        "penempatan pada bank indonesia": ["placements with bank indonesia"],
        "penempatan pada bank lain": ["placements with other banks"],
        "tagihan spot dan derivatif": ["spot and derivative forward receivables", "spot and derivative receivables"],
        "surat berharga": ["securities", "marketable securities"],
        "surat berharga yang dijual dengan janji dibeli kembali repo": [
            "securities sold under repurchase agreements repo", "securities sold under repurchase agreements"],
        "tagihan atas surat berharga yang dibeli dengan janji dijual kembali reverse repo": [
            "claims from securities purchased under resale agreements reverse repo",
            "securities purchased under resale agreements reverse repo"],
        "tagihan akseptasi": ["acceptance receivables"],
        "pinjaman yang diberikan dan piutang | kredit": ["loans", "loans and financing"],
        "pembiayaan syariah": ["sharia financing", "sharia financing receivables"],
        "penyertaan": ["equity investments", "investments"],
        "surat berharga | cadangan kerugian penurunan nilai aset keuangan": ["securities"],
        "kredit | cadangan kerugian penurunan nilai aset keuangan": ["loans and sharia financing", "loans"],
        "lainnya | cadangan kerugian penurunan nilai aset keuangan": ["others"],
        "aset tidak berwujud": ["intangible assets"],
        "akumulasi amortisasi aset tidak berwujud": ["accumulated amortization of intangible assets"],
        "aset tetap dan inventaris": ["fixed assets and equipment", "premises and equipment"],
        "akumulasi penyusutan aset tetap dan inventaris": [
            "accumulated depreciation on fixed assets and equipment", "accumulated depreciation of fixed assets"],
        "properti terbengkalai | aset non produktif": ["abandoned properties", "abandoned property"],
        "aset yang diambil alih | aset non produktif": ["foreclosed assets", "foreclosed collateral"],
        "rekening tunda | aset non produktif": ["suspense accounts"],
        "aset lainnya": ["other assets"],
        "giro": ["demand deposits", "current accounts"],
        "tabungan": ["saving deposits", "savings deposits"],
        "simpanan berjangka": ["time deposits"],
        "pinjaman dari bank indonesia": ["liabilities to bank indonesia"],
        "pinjaman dari bank lain": ["liabilities to other banks"],
        "liabilitas spot dan derivatif": ["spot and derivative forward liabilities", "spot and derivative liabilities"],
        "utang akseptasi": ["acceptance liabilities"],
        "surat berharga yang diterbitkan": ["securities issued", "debt securities issued"],
        "pinjaman yang diterima lainnya | pinjaman yang diterima": ["borrowings", "fund borrowings"],
        "setoran jaminan": ["margin deposits", "security deposits"],
        "liabilitas lainnya": ["other liabilities"],
        "modal dasar | modal disetor": ["authorized capital"],
        "modal yang belum disetor | modal disetor": ["unpaid capital"],
        "saham yang dibeli kembali treasury stock | modal disetor": ["treasury stock"],
        "agio | tambahan modal disetor": ["agio", "share premium"],
        "pendapatan kerugian komprehensif lainnya": ["other comprehensive income"],
        "cadangan umum | cadangan": ["general reserves", "reserves"],
        "tahun tahun lalu | laba rugi": ["previous years", "prior years"],
        "tahun berjalan | laba rugi": ["current year"],
        "kepentingan non pengendali": ["non controlling interest", "minority interest"],
    },
    "IS": {
        "pendapatan bunga": ["interest income"],
        "beban bunga": ["interest expense", "interest expenses"],
        "peningkatan nilai wajar aset keuangan mark to market": [
            "gain loss from increase decrease in fair value of financial assets"],
        "keuntungan penjualan aset keuangan": ["gain loss from sale of financial assets"],
        "keuntungan transaksi spot dan derivatif realised": [
            "gain loss from spot and derivative forward transactions realised"],
        "deviden": ["dividend income", "dividends"],
        "komisi provisi fee dan administrasi | pendapatan operasional selain bunga": [
            "commissions provisions fees and administrative", "fees and commissions income"],
        "pendapatan lainnya": ["other income"],
        "kerugian penurunan nilai aset keuangan impairment": ["impairment losses on financial assets",
                                                              "allowance for impairment losses on financial assets"],
        "kerugian terkait risiko operasional": ["losses related to operational risk"],
        "beban tenaga kerja": ["personnel expenses", "salaries and employee benefits"],
        "beban promosi": ["promotion expenses"],
        "beban lainnya": ["other expenses"],
        "keuntungan kerugian penjualan aset tetap dan inventaris": ["gain loss from sale of fixed assets and equipment"],
        "pendapatan beban non operasional lainnya": ["other non operating income expenses"],
        "taksiran pajak periode berjalan": ["current tax", "estimated current tax"],
        "pendapatan beban pajak tangguhan": ["deferred tax income expenses", "deferred tax"],
        "pemilik": ["owners", "owner", "equity holders of the parent"],
        "kepentingan non pemilik": ["non controlling interest", "non controlling interests"],
        "dividen": ["dividends"],
        "laba bersih per saham": ["earnings per share", "basic earnings per share"],
    },
    "CAP": {
        "modal disetor": ["paid in capital less treasury stock", "paid in capital"],
        "cadangan tambahan modal disclosed reserve": ["disclosed reserves", "additional reserves"],
        "faktor pengurang modal inti": ["deduction factor to common equity tier 1", "deduction factor"],
        "level atas upper tier 2": ["supplementary capital tier 2", "tier 2 capital"],
        "aset tertimbang menurut risiko atmr untuk risiko kredit": ["rwa credit risk", "credit risk weighted assets"],
        "aset tertimbang menurut risiko atmr untuk risiko operasional": ["rwa operational risk"],
        "aset tertimbang menurut risiko atmr untuk risiko pasar": ["rwa market risk"],
    },
}
for _sec, _d in ENGLISH_ALIASES.items():
    for _k, _v in _d.items():
        SEED_ALIASES.setdefault(_sec, {}).setdefault(_k, []).extend(_v)


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
