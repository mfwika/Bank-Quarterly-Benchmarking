import re
from functools import lru_cache


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


# '1.', '12)', 'a.', '(b)', 'iv.', 'I.' dst — enumerator dengan tanda baca
LEADING_ENUM_PATTERN = re.compile(
    r"^\s*(?:\(?[0-9]{1,3}(?:\.[0-9]{1,2})*\)?|\(?[a-zA-Z]\)?|\(?[ivxIVX]{1,6}\)?)[\.\)]\s*(?=\S)"
)
# 'a Tahun-tahun lalu', 'ii Melakukan ...', '3 Modal Inovatif', '1.1 Modal disetor'
# — enumerator tanpa titik, diikuti kata berhuruf kapital
LOOSE_ENUM_PATTERN = re.compile(r"^\s*(?:[a-z]|[ivx]{1,4}|[0-9]{1,2}(?:\.[0-9]{1,2})*)\s+(?=[A-Z(])")

ROMAN = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}


def strip_leading_enumerators(s: str) -> str:
    """Buang nomor/huruf urut di depan label (mis. '1.', 'a.', 'iv.', 'a ')."""
    prev = None
    s = str(s)
    while prev != s:
        prev = s
        s = LEADING_ENUM_PATTERN.sub("", s)
        s = LOOSE_ENUM_PATTERN.sub("", s)
    return s.strip()


def enumerator_kind(token) -> str | None:
    """Jenis penomoran: 'num' (1, 2, 12), 'letter' (a, b), 'roman' (ii, iv), None."""
    if token is None:
        return None
    t = str(token).strip().strip(".)(").strip()
    if not t:
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{1,2})*", t):
        return "num"
    if t.lower() in ROMAN and len(t) > 1:
        return "roman"
    if re.fullmatch(r"[a-zA-Z]", t):
        return "letter"
    if t.lower() in ROMAN:
        return "roman"
    return None


def leading_enumerator(s: str) -> str | None:
    m = re.match(r"^\s*\(?([0-9]{1,3}(?:\.[0-9]{1,2})*|[a-zA-Z]|[ivxIVX]{1,6})[\.\)]?\s+", str(s))
    return m.group(1) if m else None


@lru_cache(maxsize=20000)
def _clean_label_cached(s: str) -> str:
    s = strip_leading_enumerators(str(s).strip())
    s = _collapse_spaced_letters(s)
    s = s.lower().replace("-/-", " ")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_label(s) -> str:
    return _clean_label_cached(str(s))


try:
    from rapidfuzz import fuzz

    def _raw_similarity(a2: str, b2: str) -> float:
        if not a2 or not b2:
            return 0.0
        tsr = fuzz.token_sort_ratio(a2, b2)
        tset = fuzz.token_set_ratio(a2, b2)
        # partial_ratio gampang "ketipu" label pendek (mis. 'kas' ada di 'tagihan akseptasi'),
        # jadi bobotnya diturunkan kalau salah satu label sangat pendek.
        part = fuzz.partial_ratio(a2, b2)
        short = min(len(a2), len(b2))
        if short < 8:
            part *= 0.6
        # token_set_ratio 100 kalau semua kata label pendek ada di label panjang ->
        # kasih penalti kecil kalau panjangnya jauh beda. Dicampur token_sort supaya
        # urutan kata tetap berpengaruh ('surat berharga yang DIJUAL ... DIBELI kembali'
        # vs 'tagihan atas surat berharga yang DIBELI ... DIJUAL kembali').
        len_ratio = short / max(len(a2), len(b2))
        tset = tset * (0.85 + 0.15 * len_ratio)
        seq = fuzz.ratio(a2, b2)
        mixed = 0.6 * tset + 0.4 * max(tsr, seq)
        return max(tsr, mixed, part * 0.9)
except ImportError:  # pragma: no cover
    import difflib

    def _raw_similarity(a2: str, b2: str) -> float:
        if not a2 or not b2:
            return 0.0
        return difflib.SequenceMatcher(None, a2, b2).ratio() * 100


@lru_cache(maxsize=200000)
def _similarity_cached(a2: str, b2: str) -> float:
    return _raw_similarity(a2, b2)


def similarity(a, b) -> float:
    return _similarity_cached(clean_label(a), clean_label(b))


# ---------------------------------------------------------------------------------
# Angka
# ---------------------------------------------------------------------------------
_NUM_RE = re.compile(r"^(?:\(-?[0-9][0-9.,]*\)|-?[0-9][0-9.,]*)%?$")
_DASH_TOKENS = {"-", "–", "—", "--"}


def is_number_token(tok: str) -> bool:
    t = tok.strip()
    return t in _DASH_TOKENS or bool(_NUM_RE.match(t))


def parse_number(raw):
    """Parse angka format laporan Indonesia / Inggris.

    '1.234.567' -> 1234567 ; '(1.234)' -> -1234 ; '1,234,567' -> 1234567 ;
    '12,50' -> 12.5 ; '12.50%' -> 12.5 ; '-' -> 0.0
    """
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(" ", "").replace(" ", "")
    if s in _DASH_TOKENS:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    elif s.startswith("(") and s.endswith(")%"):
        neg, s = True, s[1:-2]
    s = s.rstrip("%").strip("()")
    if s.startswith("-"):
        neg, s = (not neg), s[1:]
    if not s or not re.fullmatch(r"[0-9][0-9.,]*", s):
        return None
    if "." in s and "," in s:
        groups = re.split(r"[.,]", s)
        if all(len(g) == 3 for g in groups[1:]) and 1 <= len(groups[0]) <= 3:
            s = "".join(groups)  # '15,795.918' (salah baca OCR) -> semuanya ribuan
        elif s.rfind(",") > s.rfind("."):  # separator terakhir = desimal
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "." in s or "," in s:
        sep = "." if "." in s else ","
        parts = s.split(sep)
        # semua grup setelah separator 3 digit -> separator ribuan
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]) and 1 <= len(parts[0]) <= 3:
            s = "".join(parts)
        elif len(parts) == 2:
            s = parts[0] + "." + parts[1]
        else:
            s = "".join(parts)
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v
