"""Baca laporan keuangan publikasi bank (PDF / Excel) -> daftar baris akun.

Tiap baris akun menyimpan:
  - label (nomor urut di depan sudah dibuang)
  - values: SEMUA angka di baris itu, urut dari kiri (laporan publikasi OJK
    biasanya punya 4 kolom: Bank periode ini | Bank pembanding | Konsolidasian
    periode ini | Konsolidasian pembanding)
  - section: BS / IS / CAP / COMMIT / OTHER / '?' (dari judul laporan terdekat
    di atasnya, mis. 'LAPORAN POSISI KEUANGAN', 'LAPORAN LABA RUGI', 'KPMM')
  - parent: induk akun (mis. 'Cadangan kerugian penurunan nilai' untuk
    'a. Surat berharga') supaya label kembar bisa dibedakan.
"""
import io
import re
from dataclasses import dataclass

from .periods import looks_like_period
from .text import enumerator_kind, is_number_token, parse_number, strip_leading_enumerators

SECTION_PATTERNS = [
    ("CAP", re.compile(r"PENYEDIAAN MODAL MINIMUM|KPMM|CAPITAL ADEQUACY|PERHITUNGAN MODAL|PERMODALAN|KOMPONEN MODAL"
                       r"|MINIMUM CAPITAL|CAPITAL COMPONENTS?|CAPITAL REQUIREMENT")),
    ("COMMIT", re.compile(r"KOMITMEN|KONTI[NJ]+ENSI|KONTIGENSI|COMMITMENTS?|CONTINGENC")),
    ("IS", re.compile(r"LABA\s*\(?\s*RUGI|LABA\s*/\s*RUGI|PENGHASILAN KOMPREHENSIF|INCOME STATEMENT"
                      r"|PROFIT\s*(OR|AND|&)?\s*LOSS|COMPREHENSIVE INCOME")),
    ("BS", re.compile(r"POSISI KEUANGAN|NERACA|BALANCE SHEET|FINANCIAL POSITION")),
    ("OTHER", re.compile(
        r"KUALITAS ASET|RASIO KEUANGAN|TRANSAKSI SPOT|CADANGAN PENYISIHAN|LIKUIDITAS|PENGURUS|PEMEGANG SAHAM"
        r"|ARUS KAS|PERUBAHAN EKUITAS|LEVERAGE|LIQUIDITY COVERAGE|NET STABLE|EKSPOSUR|MANAJEMEN RISIKO"
        r"|ASSET QUALITY|FINANCIAL RATIOS?|SPOT AND DERIVATIVE TRANSACTIONS|ALLOWANCE FOR|CASH FLOWS?|CHANGES IN EQUITY"
    )),
]


@dataclass
class SourceRow:
    idx: int
    label: str
    values: list
    section: str = "?"
    parent: str | None = None
    page: int | None = None
    cols: list | None = None  # per posisi angka: ((bulan, tahun) | None, 'IND'/'KONS' | None)
    ocr: bool = False  # hasil OCR (angka perlu dicek lebih teliti)
    cats: list | None = None  # kolektibilitas per kolom (L/DPK/KL/D/M/JUMLAH) di tabel kualitas aset
    ancestors: list | None = None  # semua induk (paling luar dulu)

    def value_at(self, i):
        return self.values[i] if 0 <= i < len(self.values) else None


def _heading_section(text: str):
    """Kalau baris ini judul laporan -> kode seksinya, selain itu None."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 6:
        return None
    titled = re.match(r"\s*(laporan|neraca|perhitungan|statement|report)\b", text, re.I) and len(text.split()) <= 14
    if not titled and sum(1 for c in letters if c.isupper()) / len(letters) < 0.75:
        return None
    u = text.upper()
    if re.search(r"\bUUS\b|UNIT USAHA SYARIAH", u):
        return "OTHER"  # laporan Unit Usaha Syariah: bukan laporan bank secara keseluruhan
    for key, pat in SECTION_PATTERNS:
        if pat.search(u):
            return key
    return None


_HDR_DATE = re.compile(
    r"\b(\d{1,2})\s*(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Agt|Aug|Sep|Okt|Oct|Nov|Des|Dec)[a-z]*\.?\s*(\d{4})\b", re.I)
_ENTITY_WORDS = {
    "individual": "IND", "individu": "IND", "bank": "IND", "bank only": "IND",
    "konsolidasian": "KONS", "konsolidasi": "KONS", "consolidated": "KONS",
}
_ENTITY_RE = re.compile(r"individual|individu|konsolidasian|konsolidasi|consolidated|\bbank\b", re.I)


def parse_date_header(line: str):
    """'31 Des 2025 31 Des 2024 31 Des 2025 31 Des 2024' -> [(12,2025),(12,2024),...]
    (hanya kalau baris itu memang baris header, bukan judul 'Pada Tanggal ...')."""
    from .periods import MONTHS

    found = _HDR_DATE.findall(line)
    if len(found) < 2:
        return None
    rest = _HDR_DATE.sub(" ", line)
    words = re.findall(r"[A-Za-z]{3,}", rest)
    if len(words) > 6:
        return None
    return [(MONTHS.get(m.lower()) or MONTHS.get(m.lower()[:3]), int(y)) for _, m, y in found]


def parse_entity_header(line: str):
    """'INDIVIDUAL KONSOLIDASIAN' -> ['IND','KONS']"""
    words = re.findall(r"[A-Za-z]+", line)
    hits = _ENTITY_RE.findall(line)
    if not hits or len(hits) < 0.6 * max(1, len([w for w in words if w.lower() not in ("dan", "and", "only")])):
        return None
    return [_ENTITY_WORDS.get(h.lower(), "IND") for h in hits]


_CAT_WORDS = {"l": "L", "lancar": "L", "dpk": "DPK", "kl": "KL", "d": "D", "m": "M", "macet": "M",
              "jumlah": "JUMLAH", "total": "JUMLAH", "current": "L", "sm": "DPK", "ss": "KL"}


def parse_category_header(line: str):
    """'L DPK KL D M JUMLAH L DPK KL D M JUMLAH' -> ['L','DPK','KL','D','M','JUMLAH', ...]
    (kolektibilitas di tabel Kualitas Aset Produktif)."""
    toks = re.findall(r"[A-Za-z]+", line)
    if len(toks) < 5 or re.search(r"\d", line):
        return None
    cats = [_CAT_WORDS.get(t.lower()) for t in toks]
    if any(c is None for c in cats) or "DPK" not in cats or "KL" not in cats:
        return None
    return cats


def _combine_header(dates, ents, n_values=None, cats=None):
    if cats and dates and len(cats) % len(dates) == 0:
        width = len(cats)
        per = [d for d in dates for _ in range(width // len(dates))]
        ent = (ents[0] if ents and len(set(ents)) == 1 else None)
        return [(p, ent) for p in per]
    if not dates and not ents:
        return None
    # header yg mencakup 2 tabel berdampingan ('Individual Konsolidasian' x4,
    # '31 Des 2025 31 Des 2024' x2) -> ambil pola untuk tabel kiri saja
    if ents and n_values and len(ents) > n_values and len(ents) % n_values == 0 \
            and ents == ents[:n_values] * (len(ents) // n_values):
        f = len(ents) // n_values
        ents = ents[:n_values]
        if dates and len(dates) % f == 0 and len(dates) > 1 and dates == dates[:len(dates) // f] * f:
            dates = dates[:len(dates) // f]
    m, n = len(dates or []), len(ents or [])
    width = max(m, n)
    if m and width % m:
        return None
    if n and width % n:
        return None
    per = [d for d in dates for _ in range(width // m)] if m else [None] * width
    ent = [e for e in ents for _ in range(width // n)] if n else [None] * width
    return list(zip(per, ent))


_CONT_WORDS = {"dan", "atau", "dari", "dengan", "yang", "atas", "kepada", "untuk", "pada", "selain", "dalam",
               "di", "ke", "oleh", "serta", "sebagai", "melalui", "terhadap", "tahun", "periode", "the", "of", "and"}


def _is_continuation(prev_label: str, label: str) -> bool:
    """Apakah `label` lanjutan dari baris sebelumnya yang terpotong?
    'nilai wajar aset keuangan' (huruf kecil), '(dalam satuan Rupiah)' (kurung),
    atau baris sebelumnya berakhir dengan kata sambung ('... Operasional selain')."""
    if not label:
        return False
    if label[:1].islower() or label[:1] == "(":
        return True
    last = prev_label.strip().split()[-1].lower() if prev_label.strip() else ""
    return last in _CONT_WORDS


class _RowBuilder:
    """Mengubah aliran baris (label + angka) menjadi SourceRow lengkap dengan
    seksi & induk akun."""

    def __init__(self):
        self.rows: list[SourceRow] = []
        self.section = "?"
        self.stack = []  # (level, label)
        self.pending = None  # label tanpa angka (induk / label yang terpotong)
        self.pending_closed = False
        self.last_letter = None
        self.page = None
        self.dates = None
        self.ents = None
        self.cats = None
        self.ocr_used = False

    def header_line(self, line) -> bool:
        c = parse_category_header(line)
        if c:
            self.cats = c
            return True
        d = parse_date_header(line)
        if d:
            self.dates = d
            self.cats = None
            return True
        e = parse_entity_header(line)
        if e:
            self.ents = e
            return True
        return False

    def set_page(self, page):
        self.page = page

    def _level(self, token):
        kind = enumerator_kind(token) if token else None
        if kind == "letter" and token.lower() in ("i", "v", "x") and self.last_letter != chr(ord(token.lower()) - 1):
            kind = "roman"
        if kind == "letter":
            self.last_letter = token.lower()
        if token and kind in ("letter", "roman") and token.isupper():
            return 0
        if kind == "num" and "." in token.strip("."):
            return 2  # '1.1'
        return {"num": 1, "letter": 2, "roman": 3}.get(kind, 1)

    def _push(self, level, label):
        while self.stack and self.stack[-1][0] >= level:
            self.stack.pop()
        parent = self.stack[-1][1] if self.stack and level > 0 else None
        if level > 0:
            self.stack.append((level, label))
        return parent

    def heading(self, section):
        if section != self.section:
            # tabel baru -> header kolom lama tidak berlaku lagi
            self.dates = None
            self.ents = None
            self.cats = None
        self.section = section
        self.stack = []
        self.pending = None
        self.last_letter = None

    def text_only(self, text, token=None, ends_colon=False):
        """Baris tanpa angka: judul seksi, induk akun, atau potongan label."""
        sec = _heading_section(text)
        if sec:
            self.heading(sec)
            return
        label = strip_leading_enumerators(text)
        if not re.search(r"[A-Za-z]{2,}", label):
            return
        if self.pending and not token and not self.pending_closed and _is_continuation(self.pending[1], label):
            self.pending = (self.pending[0], self.pending[1] + " " + label)
        else:
            self.pending = (token, label)
        # '... yang dapat diatribusikan kepada :' -> induk, baris berikut BUKAN lanjutan labelnya
        self.pending_closed = ends_colon

    def add(self, label, values, token=None):
        label = strip_leading_enumerators(label).strip(" .:")
        # label terpotong: 'Keuntungan (kerugian) dari ...' + baris berikut 'nilai wajar ... 1.234'
        if self.pending:
            p_token, p_label = self.pending
            if not token and not self.pending_closed and _is_continuation(p_label, label):
                label = f"{p_label} {label}"
                token = p_token
            else:
                self._push(self._level(p_token), p_label)
            self.pending = None
        if not re.search(r"[A-Za-z]{2,}", label):
            return
        parent = self._push(self._level(token), label)
        cols = _combine_header(self.dates, self.ents, len(values), self.cats)
        row = SourceRow(len(self.rows), label, list(values), self.section, parent, self.page, cols)
        row.ancestors = [lbl for _, lbl in self.stack if lbl != label]
        if self.cats and cols and len(cols) == len(self.cats):
            row.cats = list(self.cats)
        self.rows.append(row)


# ---------------------------------------------------------------------------------
# Baris teks (PDF)
# ---------------------------------------------------------------------------------
_LEAD_ENUM = re.compile(r"^\s*\(?([0-9]{1,2}(?:\.[0-9]{1,2})*|[a-zA-Z]|[ivxIVX]{1,5})[\.\)]\s*(?=\S)")


def split_label_values(line: str):
    """'12. Kredit yang diberikan 1.234 (56) - 7.890' ->
    ('12', 'Kredit yang diberikan', [1234, -56, 0, 7890]). Angka diambil dari
    UJUNG kanan baris ke kiri, jadi angka di dalam label (mis. '1,25%') aman."""
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line).strip()
    token = None
    m = _LEAD_ENUM.match(line)
    if m:
        token, line = m.group(1), line[m.end():]
    toks = line.split()
    i = len(toks)
    while i > 0 and is_number_token(toks[i - 1]):
        i -= 1
    label = " ".join(toks[:i]).strip(" .:")
    tail = toks[i:]
    # baris tanpa angka sama sekali; tapi '- - - -' (semua nol) tetap dihitung angka
    if not tail or (not any(re.search(r"\d", t) for t in tail) and len(tail) < 2):
        return token, " ".join(toks).strip(" .:"), []
    values = [parse_number(t) for t in tail]
    values = [v if v is not None else 0.0 for v in values]
    return token, label, values


_DATE_WORDS = re.compile(
    r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)[a-z]*\s*(\d{4})?\b", re.I)


def split_segments(line: str):
    """Dua tabel berdampingan dalam satu baris teks:
    'ATMR RISIKO KREDIT 835.899.197 868.520.469 Rasio CET 1 (%) 28,63% 29,24%'
    -> ['ATMR RISIKO KREDIT 835.899.197 868.520.469', 'Rasio CET 1 (%) 28,63% 29,24%']"""
    toks = line.split()
    for i in range(2, len(toks) - 1):
        if not is_number_token(toks[i - 1]) or is_number_token(toks[i]):
            continue
        run = 0
        j = i - 1
        while j >= 0 and is_number_token(toks[j]):
            run, j = run + 1, j - 1
        if run < 2 or j < 0:
            continue
        rest = toks[i:]
        if not re.match(r"[A-Za-z(]", rest[0]) or not any(is_number_token(t) and re.search(r"\d", t) for t in rest):
            continue
        return [" ".join(toks[:i])] + split_segments(" ".join(rest))
    return [line]


def _feed_text(builder: _RowBuilder, text: str):
    lines = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        if parse_date_header(raw) or parse_entity_header(raw) or parse_category_header(raw):
            lines.append(raw)
        else:
            lines.extend(split_segments(raw))
    for line in lines:
        if builder.header_line(line):
            continue
        token, label, values = split_label_values(line)
        if not values:
            if label:
                builder.text_only(label, token, ends_colon=line.rstrip().endswith(":"))
            continue
        if len(label) < 2 or looks_like_period(label) or _DATE_WORDS.search(label) \
                or re.fullmatch(r"[\d\s]*(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)\w*\.?", label, re.I):
            continue  # baris header tanggal ('30 Sep 2025 31 Des 2024')
        sec = _heading_section(label)
        if sec and len(values) <= 1:
            builder.heading(sec)
            continue
        builder.add(label, values, token)


def _count_numeric_lines(text: str) -> int:
    n = 0
    for line in (text or "").split("\n"):
        _, label, values = split_label_values(line.strip())
        if values and re.search(r"[A-Za-z]{2,}", label):
            n += 1
    return n


def _drop_ghost_spaces(page):
    """Beberapa PDF (mis. BCA, Permata) menaruh karakter spasi yang MENUMPUK di atas
    digit, sehingga '25.275.044' terbaca '2 5.275.044'. Spasi yang titik tengahnya
    jatuh di dalam karakter lain (baris yang sama) dibuang dulu."""
    try:
        chars = page.chars
    except Exception:
        return page
    solid = {}
    for c in chars:
        if c["text"].strip():
            solid.setdefault(round(c["top"]), []).append((c["x0"], c["x1"]))
    if not solid:
        return page
    for v in solid.values():
        v.sort()

    import bisect

    def inside(obj):
        mid = (obj["x0"] + obj["x1"]) / 2
        for key in (round(obj["top"]) - 1, round(obj["top"]), round(obj["top"]) + 1):
            spans = solid.get(key)
            if not spans:
                continue
            i = bisect.bisect_right(spans, (mid, float("inf")))
            for x0, x1 in spans[max(0, i - 2):i]:
                if x0 - 0.05 <= mid <= x1 + 0.05:
                    return True
        return False

    def keep(obj):
        if obj.get("object_type") != "char" or obj.get("text") != " ":
            return True
        return not inside(obj)

    return page.filter(keep)


def _find_gutter(page, x0, x1):
    """Cari 'selokan' vertikal (area kosong memanjang) di antara x0..x1."""
    try:
        words = [w for w in page.extract_words() if w["x0"] >= x0 - 1 and w["x1"] <= x1 + 1]
    except Exception:
        return None
    if len(words) < 40:
        return None
    width = int(x1 - x0) + 2
    cover = [0] * width
    for w in words:
        for x in range(max(0, int(w["x0"] - x0)), min(width, int(w["x1"] - x0) + 1)):
            cover[x] += 1
    n_lines = max(1, len({round(w["top"]) for w in words}))
    limit = max(2, int(0.03 * n_lines))
    lo, hi = int(width * 0.2), int(width * 0.8)
    best, run_start = None, None
    for x in range(lo, hi + 1):
        if cover[x] <= limit:
            run_start = x if run_start is None else run_start
            if best is None or (x - run_start) > (best[1] - best[0]):
                best = (run_start, x)
        else:
            run_start = None
    if not best or best[1] - best[0] < 6:
        return None
    return x0 + (best[0] + best[1]) / 2


def _split_columns(page, x0, x1, depth=0):
    """Pecah halaman jadi beberapa kolom (rekursif) selama tiap potongan masih
    berisi tabel (>=5 baris label+angka). Laporan di koran/web sering 2-4 kolom."""
    crop = page.crop((x0, 0, x1, page.height))
    text = crop.extract_text() or ""
    if depth >= 3:
        return [text]
    split_x = _find_gutter(page, x0, x1)
    if split_x is None:
        return [text]
    try:
        left = (page.crop((x0, 0, split_x, page.height)).extract_text() or "")
        right = (page.crop((split_x, 0, x1, page.height)).extract_text() or "")
    except Exception:
        return [text]
    if _count_numeric_lines(left) >= 5 and _count_numeric_lines(right) >= 5:
        return _split_columns(page, x0, split_x, depth + 1) + _split_columns(page, split_x, x1, depth + 1)
    return [text]


def _layout_blocks(page):
    """Susun ulang teks halaman per KOLOM TABEL berdasarkan posisi kata.

    1. kata -> 'segmen' (kata-kata berdempetan di baseline yang sama = satu frasa:
       label atau angka)
    2. awal kolom = posisi x label yang di kanannya ada angka (dikelompokkan)
    3. tiap segmen masuk ke kolom terdekat di kirinya; di dalam kolom, segmen
       disusun jadi baris dengan toleransi tinggi yang ketat (baris dari kolom lain
       yang bergeser 1-2 pt tidak ikut tergabung).
    Return list teks per kolom (atau None kalau tidak cocok dipakai)."""
    try:
        words = page.extract_words(x_tolerance=1.5, y_tolerance=1)
    except Exception:
        return None
    if len(words) < 30:
        return None
    heights = sorted(w["bottom"] - w["top"] for w in words)
    tol = max(1.0, 0.35 * heights[len(heights) // 2])  # toleransi baris ~35% tinggi huruf
    words.sort(key=lambda w: (round(w["top"] / tol), w["x0"]))
    segs = []  # dict(x0, x1, top, text)
    for w in words:
        last = segs[-1] if segs else None
        gap_limit = max(4.0, 1.4 * (w["bottom"] - w["top"]))
        if last and abs(w["top"] - last["top"]) < tol and 0 <= w["x0"] - last["x1"] < gap_limit:
            last["text"] += " " + w["text"]
            last["x1"] = w["x1"]
        else:
            segs.append({"x0": w["x0"], "x1": w["x1"], "top": w["top"], "text": w["text"]})

    def is_num(seg):
        toks = seg["text"].split()
        if len(toks) == 1 and re.fullmatch(r"\d{1,2}(\.\d{1,2})*\.", toks[0]):
            return False  # nomor urut '1.', '10.', '1.2.' -> bukan angka
        # '-' (= nol) juga angka, supaya posisi kolom tidak bergeser
        return all(is_number_token(t) for t in toks)

    by_line = {}
    for sg in segs:
        by_line.setdefault(int(sg["top"] // tol), []).append(sg)

    def same_line(sg):
        key = int(sg["top"] // tol)
        out = []
        for k in (key - 1, key, key + 1):
            out.extend(o for o in by_line.get(k, []) if abs(o["top"] - sg["top"]) < tol)
        return out

    starts = []  # (x0, top, x angka pertama) label yang langsung diikuti angka
    for sg in segs:
        if is_num(sg) or not re.search(r"[A-Za-z]{2,}", sg["text"]):
            continue
        right = sorted((o for o in same_line(sg) if o["x0"] > sg["x1"] - 1), key=lambda o: o["x0"])
        if right and is_num(right[0]):
            starts.append((sg["x0"], sg["top"], right[0]["x0"]))
        elif re.search(r"\d[\d.,]*\)?\s*$", sg["text"]):
            starts.append((sg["x0"], sg["top"], sg["x1"]))
    if len(starts) < 5:
        return None
    starts.sort()
    groups = []
    for x, top, nx in starts:
        g = groups[-1] if groups else None
        if g and x - g["xs"][-1] <= 3:
            g["xs"].append(x)
            g["tops"].append(top)
            g["nxs"].append(nx)
        else:
            groups.append({"xs": [x], "tops": [top], "nxs": [nx]})
    groups = [{"x": min(g["xs"]), "ymin": min(g["tops"]), "ymax": max(g["tops"]), "n": len(g["xs"]),
               "numx": sorted(g["nxs"])[len(g["nxs"]) // 2]} for g in groups]
    # label yang masih di KIRI angka suatu tabel = indentasi tabel itu (a., 1.2.1., dst)
    merged = []
    for g in sorted(groups, key=lambda g: g["x"]):
        host = next((m for m in merged if m["x"] <= g["x"] < m["numx"] - 5
                     and g["ymin"] <= m["ymax"] + 40 and g["ymax"] >= m["ymin"] - 40), None)
        if host:
            host["ymin"], host["ymax"] = min(host["ymin"], g["ymin"]), max(host["ymax"], g["ymax"])
            host["n"] += g["n"]
        else:
            merged.append(dict(g))
    cols_def = [g for g in merged if g["n"] >= 3]
    if not cols_def:
        return None

    def col_of(sg):
        # 1) kolom yang rentang vertikalnya benar-benar mencakup posisi ini
        # 2) kalau tidak ada: longgarkan (judul/header tabel ada di atas baris pertama)
        for lo, hi in ((2, 2), (80, 20)):
            cands = [i for i, g in enumerate(cols_def)
                     if g["x"] <= sg["x0"] + 15 and g["ymin"] - lo <= sg["top"] <= g["ymax"] + hi]
            if cands:
                return max(cands, key=lambda i: cols_def[i]["x"])
        cands = [i for i, g in enumerate(cols_def) if g["x"] <= sg["x0"] + 15] or [0]
        return max(cands, key=lambda i: cols_def[i]["x"])

    order = sorted(range(len(cols_def)), key=lambda i: (cols_def[i]["x"], cols_def[i]["ymin"]))
    cols = {i: [] for i in order}
    label_col = {}
    for sg in segs:
        if not is_num(sg):
            label_col[id(sg)] = col_of(sg)
    for sg in segs:
        if is_num(sg):
            # angka ikut kolom LABA-nya: label terdekat di kiri pada baris yang sama
            left = [o for o in same_line(sg) if not is_num(o) and o["x1"] <= sg["x0"] + 1
                    and re.search(r"[A-Za-z]{2,}", o["text"])]
            if left:
                cols[label_col[id(max(left, key=lambda o: o["x1"]))]].append(sg)
                continue
            cols[col_of(sg)].append(sg)
        else:
            cols[label_col[id(sg)]].append(sg)
    cols = [cols[i] for i in order]

    blocks = []
    for col in cols:
        col.sort(key=lambda o: (o["top"], o["x0"]))
        lines, cur, cur_top = [], [], None
        for sg in col:
            if cur and abs(sg["top"] - cur_top) >= tol:
                lines.append(" ".join(o["text"] for o in sorted(cur, key=lambda o: o["x0"])))
                cur = []
            cur.append(sg)
            cur_top = sum(o["top"] for o in cur) / len(cur)  # rata-rata: toleran baris miring
        if cur:
            lines.append(" ".join(o["text"] for o in sorted(cur, key=lambda o: o["x0"])))
        blocks.append("\n".join(lines))
    return blocks


def _page_blocks(page):
    """Laporan publikasi di koran/web sering multi-kolom (Neraca | Laba Rugi | ...).
    Kalau ada 'selokan' vertikal yang jelas, halaman dipecah per kolom supaya baris
    dari kolom yang berbeda tidak tercampur."""
    try:
        old = _split_columns(page, 0, page.width)
    except Exception:
        old = [page.extract_text() or ""]
    new = _layout_blocks(page)
    if new is None:
        return old
    # pilih susunan yang menghasilkan lebih banyak baris lengkap:
    # label + angka + header kolom (periode/entitas) yang jumlahnya pas
    return new if _blocks_quality(new) > _blocks_quality(old) else old


def _blocks_quality(blocks) -> float:
    b = _RowBuilder()
    for text in blocks:
        _feed_text(b, text)
    score = 0.0
    for r in b.rows:
        if not r.values:
            continue
        if r.cols and any(p for p, _ in r.cols):
            if len(r.cols) == len(r.values):
                score += 1.0
            elif len(r.values) < len(r.cols):
                score += 0.6
            else:
                score -= 0.5  # angka lebih banyak dari kolom header -> baris tercampur
        else:
            score += 0.2
    return score


# ---------------------------------------------------------------------------------
# OCR (untuk PDF yang tabelnya berupa GAMBAR, mis. hasil scan / export gambar)
# ---------------------------------------------------------------------------------
def ocr_available() -> bool:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def clean_ocr_text(text: str) -> str:
    """Rapikan salah baca OCR yang umum di tabel angka."""
    out = []
    for line in text.split("\n"):
        line = line.replace("|", " ").replace("¢", "").replace("—", "-").replace("–", "-")
        line = re.sub(r"[\]\}\[\{]+", " ", line)  # '44,027,008]' / '[Personnel' -> noise OCR
        line = re.sub(r"(\d[.,]) (\d{3})(?!\d)", r"\1\2", line)  # '1.379, 647' -> '1.379,647'
        # '27,981 308' -> '27,981,308' (pemisah ribuan terbaca spasi)
        line = re.sub(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+) (\d{3})(?![\d.,])", r"\1,\2", line)
        # '47 778,404' -> '47,778,404'
        line = re.sub(r"(?<![\w.,])(\d{1,3}) (\d{3}(?:[.,]\d{3})+)(?![\d.,])", r"\1,\2", line)
        # kurung nyasar: '2,973,145)' tanpa '(' -> '2,973,145' ; '(Securities' -> 'Securities'
        line = re.sub(r"(?<![(\d.,])(\d[\d.,]*\d)\)", r"\1", line)
        line = re.sub(r"\((?=[A-Za-z]{3,}\b)(?![^()]*\))", "", line)
        out.append(re.sub(r"\s{2,}", " ", line).strip())
    return "\n".join(out)


def _ocr_page_blocks(page, lang="ind+eng"):
    """OCR tiap gambar tabel di halaman (urut kolom kiri->kanan, atas->bawah).
    Kalau tidak ada gambar besar, seluruh halaman di-OCR."""
    import pytesseract

    area = page.width * page.height
    imgs = [im for im in page.images
            if (im["x1"] - im["x0"]) * (im["bottom"] - im["top"]) > 0.02 * area]
    regions = [(im["x0"], im["top"], im["x1"], im["bottom"]) for im in imgs] or [(0, 0, page.width, page.height)]
    regions.sort(key=lambda b: (round(b[0] / 50), b[1]))
    texts = []
    for x0, top, x1, bottom in regions:
        try:
            crop = page.crop((max(0, x0), max(0, top), min(page.width, x1), min(page.height, bottom)))
            img = crop.to_image(resolution=350).original
            try:
                txt = pytesseract.image_to_string(img, lang=lang, config="--psm 6")
            except pytesseract.TesseractError:
                txt = pytesseract.image_to_string(img, config="--psm 6")
            texts.append(clean_ocr_text(txt))
        except Exception:
            continue
    return texts


def parse_pdf(file_bytes: bytes, allow_ocr: bool = True):
    """-> (rows, full_text)"""
    import pdfplumber

    builder = _RowBuilder()
    texts = []
    use_ocr = allow_ocr and ocr_available()
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            builder.set_page(pno)
            page = _drop_ghost_spaces(page)
            blocks = _page_blocks(page)
            if use_ocr and sum(_count_numeric_lines(b) for b in blocks) < 3 and page.images:
                ocr_blocks = _ocr_page_blocks(page)
                if sum(_count_numeric_lines(b) for b in ocr_blocks) >= 3:
                    blocks = ocr_blocks
                    builder.ocr_used = True
            for block in blocks:
                texts.append(block)
                _feed_text(builder, block)
            # fallback: halaman yang teksnya gagal dibaca per baris -> coba ekstraksi tabel
            if sum(_count_numeric_lines(b) for b in blocks) < 3:
                try:
                    for table in page.extract_tables():
                        for row in table:
                            cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
                            if len(cells) >= 2:
                                _feed_text(builder, " ".join(cells))
                except Exception:
                    pass
    for r in builder.rows:
        r.ocr = builder.ocr_used
    return builder.rows, "\n".join(texts)


# ---------------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------------
def parse_excel(file_bytes: bytes):
    import warnings

    import openpyxl

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    builder = _RowBuilder()
    texts = []
    try:
        for ws in wb.worksheets:
            builder.heading(_heading_section(ws.title.upper() + " LAPORAN") or "?")
            for row in ws.iter_rows(values_only=True):
                token, label, values = None, None, []
                for v in row:
                    if v is None or (isinstance(v, str) and not v.strip()):
                        continue
                    if isinstance(v, str):
                        s = v.strip()
                        if label is not None and is_number_token(s):
                            num = parse_number(s)
                            values.append(0.0 if num is None else num)
                        elif label is None and len(s) <= 5 and enumerator_kind(s):
                            token = s.strip(".)(")
                        elif not looks_like_period(s):
                            if label is None or (not values and len(s) > len(label)):
                                label = s
                    elif isinstance(v, (int, float)) and not isinstance(v, bool):
                        if label is None and float(v).is_integer() and 0 < v < 100 and token is None:
                            token = str(int(v))
                        elif label is not None:
                            values.append(float(v))
                if not label:
                    continue
                texts.append(label)
                if values:
                    sec = _heading_section(label)
                    if sec and len(values) <= 1:
                        builder.heading(sec)
                    else:
                        builder.add(label, values, token)
                else:
                    builder.text_only(label, token)
    finally:
        wb.close()
    return builder.rows, "\n".join(texts)


def parse_source(filename: str, file_bytes: bytes):
    if filename.lower().endswith(".pdf"):
        return parse_pdf(file_bytes)
    return parse_excel(file_bytes)
