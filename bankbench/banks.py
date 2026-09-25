"""Tebak laporan yang di-upload itu milik bank yang mana (-> sheet template)."""
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
    "Permata": ["BANK PERMATA"],
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


def _keywords_for(model):
    kws = list(BANK_KEYWORDS.get(model.name, []))
    bn = (model.bank_name or "").upper().strip()
    if bn and bn != model.name.upper() and len(bn) > 5:
        kws.append(bn)
    return kws


def detect_bank(text: str, source_rows, models: dict, aliases: dict):
    """Skor tiap sheet = kecocokan nama bank di teks laporan + jumlah angka laporan
    yang persis sama dengan histori sheet tsb (paling bisa diandalkan).
    Return list (sheet, skor, alasan) urut dari skor tertinggi."""
    head = re.sub(r"\s+", " ", (text or "")[:20000].upper())
    out = []
    for name, model in models.items():
        kw_hits = sum(head.count(k) for k in _keywords_for(model))
        latest = model.latest_period()
        m = Matcher(model, source_rows, model.last_period_col() + 1, aliases)
        anchors = len(m._find_anchors(1.0))
        score = anchors * 2 + min(kw_hits, 5) * 10 + ((latest[1] * 12 + latest[0]) / 1e4 if latest else 0)
        reason = f"{anchors} angka cocok dgn histori, nama bank {'ditemukan' if kw_hits else 'tidak ditemukan'}"
        out.append((name, score, reason))
    out.sort(key=lambda x: x[1], reverse=True)
    return out


def sheet_display(model):
    latest = model.latest_period()
    tail = f" — data s/d {latest[0]:02d}/{latest[1]}" if latest else ""
    bn = model.bank_name if clean_label(model.bank_name) != clean_label(model.name) else ""
    return f"{model.name}{' (' + bn + ')' if bn else ''}{tail}"
