"""Tebak laporan yang di-upload itu milik bank yang mana (-> sheet template)."""
import os
import re

from .matcher import Matcher
from .text import clean_label

BANK_KEYWORDS = {
    "Mandiri": ["BANK MANDIRI"],
    "BRI": ["BANK RAKYAT INDONESIA"],
    "BCA": ["BANK CENTRAL ASIA"],
    "BNI": ["BANK NEGARA INDONESIA"],
    "CIMB": ["CIMB NIAGA"],
    "Panin": ["PAN INDONESIA", "PANIN"],
    "Permata": ["BANK PERMATA", "PERMATABANK"],
    "BII": ["MAYBANK INDONESIA", "BANK INTERNASIONAL INDONESIA", "MAYBANK"],
    "BTN": ["BANK TABUNGAN NEGARA"],
    "OCBC NISP": ["OCBC NISP", "OCBC INDONESIA", "BANK OCBC"],
    "DBS": ["DBS INDONESIA"],
    "Mega": ["BANK MEGA"],
    "Bukopin": ["BUKOPIN", "KB BANK"],
    "HSBC": ["HSBC"],
    "Citibank": ["CITIBANK"],
    "Danamon": ["DANAMON"],
    "BSI": ["BANK SYARIAH INDONESIA"],
    "BTPN inc SMBC": ["BTPN", "SMBC INDONESIA"],
    "Bangkok": ["BANGKOK BANK"],
}

# singkatan yang lazim dipakai di nama file ("BNI-Financial-Statement-1H2026.pdf")
FILE_KEYWORDS = {
    "Mandiri": ["MANDIRI"], "BRI": ["BRI"], "BCA": ["BCA"], "BNI": ["BNI"], "CIMB": ["CIMB"],
    "Panin": ["PANIN"], "Permata": ["PERMATA"], "BII": ["MAYBANK", "BII"], "BTN": ["BTN"],
    "OCBC NISP": ["OCBC", "NISP"], "DBS": ["DBS"], "Mega": ["MEGA"], "Bukopin": ["BUKOPIN", "KBBANK"],
    "HSBC": ["HSBC"], "Citibank": ["CITI", "CITIBANK"], "Danamon": ["DANAMON"], "BSI": ["BSI"],
    "BTPN inc SMBC": ["BTPN", "SMBC"], "Bangkok": ["BANGKOK"],
}


def _keywords_for(model):
    kws = list(BANK_KEYWORDS.get(model.name, []))
    bn = (model.bank_name or "").upper().strip()
    if bn and bn != model.name.upper() and len(bn) > 5:
        kws.append(bn)
    return kws


def detect_bank(text: str, source_rows, models: dict, aliases: dict, filename: str = ""):
    """Skor tiap sheet = jumlah angka laporan yang persis sama dengan histori sheet tsb (paling bisa
    diandalkan) + nama bank di judul tabel ('PT Bank ...'), di teks laporan, dan di nama file.
    Laporan hasil scan (OCR) sering tanpa teks -> judul tabel hasil OCR & nama file jadi penentu.
    Return list (sheet, skor, alasan) urut dari skor tertinggi."""
    head = re.sub(r"\s+", " ", (text or "")[:20000].upper())
    titles = re.sub(r"\s+", " ", " ".join(sorted({(getattr(r, "company", None) or "") for r in source_rows})).upper())
    ftoks = set(re.findall(r"[A-Z]+", re.sub(r"(?<=[a-z])(?=[A-Z])", " ", os.path.basename(filename or "")).upper()))
    out = []
    for name, model in models.items():
        kws = _keywords_for(model)
        kw_hits = sum(head.count(k) for k in kws)
        title_hit = any(k in titles for k in kws)
        file_hit = bool(ftoks & set(FILE_KEYWORDS.get(name, [])))
        latest = model.latest_period()
        # kolom setelah periode TERBARU (bukan kolom paling kanan: ada sheet dengan kolom catatan
        # 'Dec 18' jauh di kanan berisi rumus)
        lc = model.find_period_col(*latest) if latest else None
        m = Matcher(model, source_rows, (lc or model.last_period_col()) + 1, aliases, period=(12, 1900))
        anchors = max(len(m._find_anchors(sc)) for sc in (1.0, 0.001, 1000.0))  # laporan juta vs template miliar
        score = (anchors * 2 + min(kw_hits, 5) * 10 + title_hit * 30 + file_hit * 25
                 + ((latest[1] * 12 + latest[0]) / 1e4 if latest else 0))
        why = [f"{anchors} angka cocok dgn histori"]
        if title_hit:
            why.append("nama bank di judul tabel")
        if kw_hits:
            why.append("nama bank di teks")
        if file_hit:
            why.append("nama file")
        if len(why) == 1:
            why.append("nama bank tidak ditemukan")
        out.append((name, score, ", ".join(why)))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def sheet_display(model):
    latest = model.latest_period()
    tail = f" — data s/d {latest[0]:02d}/{latest[1]}" if latest else ""
    bn = model.bank_name if clean_label(model.bank_name) != clean_label(model.name) else ""
    return f"{model.name}{' (' + bn + ')' if bn else ''}{tail}"
