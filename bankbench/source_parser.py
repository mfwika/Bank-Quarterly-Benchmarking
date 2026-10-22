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
    company: str | None = None  # 'PT Bank X ...' di judul tabelnya (laporan grup induk di halaman yang sama)
    group: str | None = None  # file OJK: 'OJK|<bank>|<bulan>/<tahun>' -> file-file satu laporan digabung

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
    if re.search(r"\bUUS\b|(UNIT|BISNIS) USAHA SYARIAH|SHARIA BUSINESS UNIT|SHARIA UNIT", u):
        return "OTHER"  # laporan Unit Usaha Syariah: bukan laporan bank secara keseluruhan
    for key, pat in SECTION_PATTERNS:
        if pat.search(u):
            return key
    # judul ditulis berspasi per huruf ('L A P O R A N  P O S I S I  K E U A N G A N')
    if re.search(r"(\b[A-Z] ){4,}", u):
        compact = re.sub(r"\s+", "", u)
        for key, pat in SECTION_PATTERNS:
            if re.search(pat.pattern.replace(" ", r"\s*"), compact):
                return key
    return None


_HDR_DATE = re.compile(
    r"\b(\d{1,2})\s*(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Agt|Aug|Sep|Okt|Oct|Nov|Des|Dec)[a-z]*\.?\s*(\d{4})\b", re.I)
_ENTITY_WORDS = {
    "individual": "IND", "individu": "IND", "bank": "IND", "bank only": "IND",
    "konsolidasian": "KONS", "konsolidasi": "KONS", "consolidated": "KONS",
}
_ENTITY_RE = re.compile(r"individual|individu|konsolidasian|konsolidasi|consolidated|\bbank\b", re.I)


_HDR_DATE_EN = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})\b", re.I)


def _find_dates(line: str):
    """[(hari, bulan, tahun)] urut posisi: '31 Des 2025' maupun 'December 31, 2025'."""
    hits = [(m.start(), (m.group(1), m.group(2), m.group(3))) for m in _HDR_DATE.finditer(line)]
    hits += [(m.start(), (m.group(2), m.group(1), m.group(3))) for m in _HDR_DATE_EN.finditer(line)
             if not any(abs(m.start() - h[0]) < 3 for h in hits)]
    return [h[1] for h in sorted(hits)]


def _is_period_start_line(line: str) -> bool:
    """'1 JAN 2026 1 JAN 2026' = awal periode di header bertumpuk ('1 Jan 2026 s/d 30 Jun 2026')."""
    found = _find_dates(line)
    return bool(found) and all(int(d) == 1 and m.lower().startswith("jan") for d, m, _ in found)


def _stack_dates(stack):
    """Header bertumpuk: '30 JUN 2025 30 JUN 2025' lalu '30 JUN 2026 30 JUN 2026' (kolom saling
    selang-seling, baris tanggal beda tinggi) -> per blok: periode terbaru dulu, lalu pembanding."""
    k = len(stack[0])
    if any(len(x) != k for x in stack):
        return stack[-1]
    out = []
    for j in range(k):
        group = sorted({x[j] for x in stack}, key=lambda p: (p[1], p[0]), reverse=True)
        out.extend(group)
    return out


def parse_date_header(line: str):
    """'31 Des 2025 31 Des 2024 31 Des 2025 31 Des 2024' -> [(12,2025),(12,2024),...]
    (hanya kalau baris itu memang baris header, bukan judul 'Pada Tanggal ...')."""
    from .periods import MONTHS

    found = _find_dates(line)
    if len(found) < 2:
        return None
    rest = _HDR_DATE_EN.sub(" ", _HDR_DATE.sub(" ", line))
    rest = re.sub(r"\([^()]*\)?", " ", rest)  # '(Direviu)', '(Tidak Direviu & Tidak Diaudit)'
    rest = re.sub(r"\b(tidak|direviu|diaudit|audited|unaudited|reviewed|not)\b", " ", rest, flags=re.I)
    words = re.findall(r"[A-Za-z]{3,}", rest)
    if len(words) > 6:
        return None
    return [(MONTHS.get(m.lower()) or MONTHS.get(m.lower()[:3]), int(y)) for _, m, y in found]


def parse_year_header(line: str):
    """'No. POS-POS 2025 2024' (header hanya tahun) -> [2025, 2024]."""
    if _find_dates(line):
        return None
    years = re.findall(r"(?<![\d.,])(?:19|20)\d{2}(?![\d.,])", line)
    if len(years) < 2:
        return None
    rest = re.sub(r"(?<![\d.,])(?:19|20)\d{2}(?![\d.,])", " ", line)
    words = {w.lower() for w in re.findall(r"[A-Za-z]{2,}", rest)}
    header_words = {"no", "pos", "description", "keterangan", "uraian", "items", "item", "bank", "individual",
                    "konsolidasian", "consolidated", "komponen", "modal", "rasio", "ratio", "account", "accounts"}
    if re.search(r"\d", rest) or not words <= header_words:
        return None  # baris akun yang angkanya kebetulan mirip tahun ('Laba per saham 2015 2020')
    return [int(y) for y in years]


def parse_entity_header(line: str):
    """'INDIVIDUAL KONSOLIDASIAN' -> ['IND','KONS']"""
    first = _ENTITY_RE.search(line)
    if first and first.start() > 0 and not re.search(r"\d", line) \
            and len(_ENTITY_RE.findall(line)) >= 2:
        # 'NO KOMPONEN MODAL Individual Konsolidasian ...' -> judul kolom label di kiri diabaikan
        line = line[first.start():]
    # 'BANK CIMB NIAGA CONSOLIDATED' -> nama bank di antara 'BANK' dan kolom berikutnya diabaikan
    line = re.sub(r"\b(bank)\b((?:\s+(?!konsolidasi|consolidated|individu|bank\b)[A-Za-z]+){1,3})(?=\s+(konsolidasi|consolidated))",
                  r"\1", line, flags=re.I)
    words = re.findall(r"[A-Za-z]+", line)
    hits = _ENTITY_RE.findall(line)
    if not hits or len(hits) < 0.6 * max(1, len([w for w in words if w.lower() not in ("dan", "and", "only")])):
        return None
    return [_ENTITY_WORDS.get(h.lower(), "IND") for h in hits]


_CAT_WORDS = {"l": "L", "lancar": "L", "dpk": "DPK", "kl": "KL", "d": "D", "m": "M", "macet": "M",
              "jumlah": "JUMLAH", "total": "JUMLAH", "current": "L", "sm": "DPK", "ss": "KL",
              # header Inggris 2 baris: 'Special Sub' di atas 'Current Mention Standard Doubtful Loss Total'
              "mention": "DPK", "standard": "KL", "substandard": "KL", "doubtful": "D", "loss": "M"}
_CAT_SKIP = {"special", "sub"}


def parse_category_header(line: str):
    """'L DPK KL D M JUMLAH L DPK KL D M JUMLAH' -> ['L','DPK','KL','D','M','JUMLAH', ...]
    (kolektibilitas di tabel Kualitas Aset Produktif)."""
    toks = re.findall(r"[A-Za-z]+", line)
    if len(toks) < 5 or re.search(r"\d", line):
        return None
    toks = [t for t in toks if t.lower() not in _CAT_SKIP]
    cats = [_CAT_WORDS.get(t.lower()) for t in toks]
    if any(c is None for c in cats) or "DPK" not in cats or "KL" not in cats:
        return None
    return cats


def _repair_cat_groups(values, cats):
    """Tabel kolektibilitas dengan sel '-' yang tidak ikut terbaca ('613.019 - - - 613.019' padahal
    ada 5 kolom + JUMLAH): pecah per kelompok [L .. M, JUMLAH] memakai JUMLAH = jumlah isinya,
    lalu sel yang hilang diisi 0 tepat sebelum JUMLAH. None kalau tidak bisa dipastikan."""
    if "JUMLAH" not in cats:
        return None
    g = cats.index("JUMLAH") + 1
    if len(cats) % g or any(cats[i:i + g] != cats[:g] for i in range(0, len(cats), g)):
        return None
    ngroups = len(cats) // g

    def solve(pos, left):
        if left == 0:
            return [] if pos == len(values) else None
        for k in range(g - 1, 0, -1):  # sel hilang paling sedikit dulu
            j = pos + k
            if j >= len(values):
                continue
            part = values[pos:j]
            if abs(sum(part) - values[j]) <= 1.0 and (values[j] != 0 or k == g - 1 or left > 1):
                rest = solve(j + 1, left - 1)
                if rest is not None:
                    return part + [0.0] * (g - 1 - k) + [values[j]] + rest
        return None

    out = solve(0, ngroups)
    return out if out and len(out) == len(cats) else None


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
    out = list(zip(per, ent))
    if m and n and len(set(out)) < len(out):
        # (periode, entitas) dobel = baris tanggal milik 2 tabel berdampingan -> pakai blok pertama
        for k in range(1, m):
            if m % k == 0 and dates == dates[:k] * (m // k) and width % k == 0:
                return _combine_header(dates[:k], ents, n_values, cats)
    return out


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
        self.date_stack = None  # baris-baris tanggal header sejak baris angka terakhir

    def header_line(self, line) -> bool:
        found = _find_dates(line)
        if found and not re.search(r"\d[.,]\d{3}", line):
            # judul '31 Desember 2025 dan 2024' / '30 Juni 2026 dan 31 Desember 2025': bulan per tahun
            from .periods import MONTHS
            self.title_months = {int(y): (MONTHS.get(m.lower()) or MONTHS.get(m.lower()[:3])) for _, m, y in found}
            self.title_months.setdefault(0, next(iter(self.title_months.values())))
        ys = parse_year_header(line)
        if ys:
            tm = getattr(self, "title_months", None) or {}
            dflt = tm.get(0) or 12
            new = [(tm.get(y, dflt), y) for y in ys]
            if new != self.dates:  # header halaman lanjutan (tanggal sama) -> kategori kolektibilitas tetap
                self.cats = None
            self.dates = new
            self.date_stack = None
            return True
        c = parse_category_header(line)
        if c:
            self.cats = c
            return True
        d = parse_date_header(line)
        if d:
            if _is_period_start_line(line):
                return True
            self.date_stack = (self.date_stack or []) + [d]
            new = _stack_dates(self.date_stack) if len(self.date_stack) > 1 else d
            if new != self.dates:
                self.cats = None
            self.dates = new
            return True
        e = parse_entity_header(line)
        if e:
            self.ents = e
            return True
        return False

    def _merge_ocr_thousands(self, values):
        """OCR: '484,545 422,706' terbaca '484 545 422 706' -> gabung kelompok 3 digit sampai jumlah
        angka = jumlah kolom."""
        width = max(len(self.dates or []), len(self.ents or []))
        if not (self.ocr_used and width and len(values) > width):
            return values
        out, i = [], 0
        extra = len(values) - width
        while i < len(values):
            a = values[i]
            if extra and i + 1 < len(values):
                b = values[i + 1]
                if a == int(a) and b == int(b) and 0 < abs(a) < 1000 and 100 <= abs(b) < 1000:
                    out.append(float((abs(a) * 1000 + abs(b)) * (1 if a > 0 else -1)))
                    i += 2
                    extra -= 1
                    continue
            out.append(a)
            i += 1
        return out if len(out) == width else values

    def _merge_split_digit(self, values):
        """'4 9,112' (digit pertama terpisah spasi) -> 49,112, hanya kalau jumlah angka lebih satu
        dari jumlah kolom header."""
        width = max(len(self.dates or []), len(self.ents or []))
        if not width or len(values) != width + 1:
            return values
        for i in range(len(values) - 1):
            a, b = values[i], values[i + 1]
            if a == int(a) and 0 < a < 10 and b == int(b) and 1000 <= b < 100000:
                merged = int(a) * 10 ** len(str(int(b))) + b
                return values[:i] + [float(merged)] + values[i + 2:]
        return values

    def set_page(self, page, head_text=""):
        self.page = page
        self.company = None  # nama perusahaan di judul tabel berlaku sampai akhir halaman
        # halaman Unit Usaha Syariah (judul kecil di atas 'LAPORAN POSISI KEUANGAN') -> abaikan sehalaman
        self.uus_page = bool(re.search(r"\bUUS\b|(UNIT|BISNIS) USAHA SYARIAH|SHARIA BUSINESS UNIT|SHARIA UNIT", head_text.upper()))
        if self.uus_page:
            self.heading("OTHER")

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
        if getattr(self, "uus_page", False) or getattr(self, "uus_block", False):
            section = "OTHER"
        if section != self.section:
            # tabel baru -> header kolom lama tidak berlaku lagi
            self.dates = None
            self.date_stack = None
            self.ents = None
            self.cats = None
        self.section = section
        self.stack = []
        self.pending = None
        self.last_letter = None

    def text_only(self, text, token=None, ends_colon=False):
        """Baris tanpa angka: judul seksi, induk akun, atau potongan label."""
        if re.match(r"\W*PT\.?\s+BANK\s+\w", text, re.I) and len(text.split()) <= 12:
            self.company = text.strip()
        sec = _heading_section(text)
        if sec:
            title = re.sub(r"\s+", " ", text.upper()).strip()
            if title != getattr(self, "last_title", None):
                self.cats = None  # tabel lain (judul beda) -> kategori kolektibilitas tidak berlaku
            self.last_title = title
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
        if len(values) == 1 and values[0] in (1.0, 2.0, 3.0) \
                and re.search(r"\b(CET|AT|Tier|Level|Kelompok|Group)$", label.strip(), re.I):
            # 'Deduction Factor of Common Equity Tier 1' = judul kelompok, bukan angka
            self.text_only(f"{label.strip()} {int(values[0])}", token)
            return
        # label terpotong: 'Keuntungan (kerugian) dari ...' + baris berikut 'nilai wajar ... 1.234'
        values = list(values)
        width = max(len(self.dates or []), len(self.ents or []))
        if not width:
            # header kolom tidak terbaca (OCR): jumlah kolom = yang paling sering di baris-baris terakhir
            recent = getattr(self, "recent_lens", [])
            width = max(set(recent), key=recent.count) if len(recent) >= 3 else 0
        if width and len(values) == width + 1 and (values[0] in (1.0, 2.0, 3.0) or
                                                   (self.ocr_used and values[0] in (11.0, 12.0, 21.0))) \
                and re.search(r"\b(CET|AT|Tier|Level|Kelompok|Group)$", label.strip(), re.I):
            # 'CET 1' / 'Tier 2' bagian dari nama akun ('Tier 21' = OCR '2' + garis tabel)
            label, values = f"{label.strip()} {str(int(values[0]))[0]}", values[1:]
        values = self._merge_split_digit(values)
        values = self._merge_ocr_thousands(values)
        self.recent_lens = (getattr(self, "recent_lens", []) + [len(values)])[-10:]
        if self.ocr_used and width and len(values) > width:
            nonzero = [v for v in values if v != 0]
            if len(nonzero) == width:
                values = nonzero  # '-' nyasar hasil OCR ('16.935.370 - 16.935.370') -> angka 0 palsu
        if self.pending:
            p_token, p_label = self.pending
            if not token and not re.search(r"[A-Za-z]{2,}", label):
                # label panjang di baris sendiri, angkanya di baris berikut (tanpa label)
                label, token = p_label, p_token
            elif not token and not self.pending_closed and _is_continuation(p_label, label):
                label = f"{p_label} {label}"
                token = p_token
            else:
                self._push(self._level(p_token), p_label)
            self.pending = None
        if not re.search(r"[A-Za-z]{2,}", label):
            return
        if self.section != "CAP" and len(label) < 40 and re.search(r"\b(Modal Inti \(?Tier 1|Core Capital \(?Tier 1)", label, re.I):
            self.heading("CAP")  # judul tabel KPMM tidak terbaca (OCR) -> baris pertamanya khas
        parent = self._push(self._level(token), label)
        self.date_stack = None
        if self.cats and len(values) < len(self.cats):
            values = _repair_cat_groups(values, self.cats) or values
        cols = _combine_header(self.dates, self.ents, len(values), self.cats)
        row = SourceRow(len(self.rows), label, list(values), self.section, parent, self.page, cols)
        row.ancestors = [lbl for _, lbl in self.stack if lbl != label]
        row.company = getattr(self, "company", None)
        if self.cats and cols and len(cols) == len(self.cats):
            row.cats = list(self.cats)
            if self.ocr_used:
                # tabel kolektibilitas tidak punya angka negatif: '(83,729' = '183,729' (angka 1 terbaca '(')
                row.values = [float("1" + str(int(abs(v)))) if v < 0 and v == int(v) else v for v in row.values]
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


_UUS_RE = re.compile(r"\bUUS\b|(UNIT|BISNIS) USAHA SYARIAH|SHARIA BUSINESS UNIT|SHARIA UNIT")


def _feed_text(builder: _RowBuilder, text: str):
    # judul 'INFORMASI KEUANGAN BISNIS USAHA SYARIAH' di halaman koran: semua tabel di bawahnya (Neraca,
    # Laba Rugi UUS, dst. dengan sub-judulnya sendiri) bukan laporan bank -> berlaku sampai akhir blok
    builder.uus_block = False
    lines = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        if parse_date_header(raw) or parse_year_header(raw) or parse_entity_header(raw) or parse_category_header(raw):
            lines.append(raw)
        else:
            lines.extend(split_segments(raw))
    for line in lines:
        if not builder.uus_block and _UUS_RE.search(line.upper()) and _heading_section(line) == "OTHER":
            builder.uus_block = True
            builder.heading("OTHER")
            continue
        if builder.header_line(line):
            continue
        token, label, values = split_label_values(line)
        if not values:
            if label:
                builder.text_only(label, token, ends_colon=line.rstrip().endswith(":"))
            continue
        if len(label) < 2 and len(values) >= 2 and builder.pending and not builder.pending_closed:
            builder.add(label, values, token)  # angka milik label panjang di baris sebelumnya
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


def _layout_blocks(page, v2=False):
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
            run = []
            for o in right:
                if not is_num(o):
                    break
                run.append(o)
            starts.append((sg["x0"], sg["top"], right[0]["x0"], run[-1]["x1"]))
        elif re.search(r"\d[\d.,]*\)?\s*$", sg["text"]):
            starts.append((sg["x0"], sg["top"], sg["x1"], sg["x1"]))
    if len(starts) < 5:
        return None
    starts.sort()
    groups = []
    for x, top, nx, nx1 in starts:
        g = groups[-1] if groups else None
        if g and x - g["xs"][-1] <= 3:
            g["xs"].append(x)
            g["tops"].append(top)
            g["nxs"].append(nx)
            g["nx1s"].append(nx1)
        else:
            groups.append({"xs": [x], "tops": [top], "nxs": [nx], "nx1s": [nx1]})
    groups = [{"x": min(g["xs"]), "ymin": min(g["tops"]), "ymax": max(g["tops"]), "n": len(g["xs"]),
               "numx": sorted(g["nxs"])[len(g["nxs"]) // 2], "numx1": max(g["nx1s"])} for g in groups]
    # label yang masih di KIRI angka suatu tabel = indentasi tabel itu (a., 1.2.1., dst)
    merged = []
    for g in sorted(groups, key=lambda g: g["x"]):
        host = next((m for m in merged if m["x"] <= g["x"] < m["numx"] - 5
                     and g["ymin"] <= m["ymax"] + 40 and g["ymax"] >= m["ymin"] - 40), None)
        if host:
            host["ymin"], host["ymax"] = min(host["ymin"], g["ymin"]), max(host["ymax"], g["ymax"])
            host["n"] += g["n"]
            host["numx1"] = max(host["numx1"], g["numx1"])
        else:
            merged.append(dict(g))
    cols_def = [g for g in merged if g["n"] >= 3]
    if not cols_def:
        return None

    def col_of(sg, label=False):
        # 1) kolom yang rentang vertikalnya benar-benar mencakup posisi ini
        # 2) kalau tidak ada: longgarkan (judul/header tabel ada di atas baris pertama)
        # label yang mulai di KANAN awal angka suatu tabel bukan label tabel itu (tabel sebelah
        # yang baris pertamanya lebih rendah, mis. 'I. PIHAK TERKAIT' di samping 'Kas 1.668.496')
        for lo, hi in ((2, 2), (80, 20)):
            cands = [i for i, g in enumerate(cols_def)
                     if g["x"] <= sg["x0"] + 15 and g["ymin"] - lo <= sg["top"] <= g["ymax"] + hi
                     and not (v2 and label and sg["x0"] > g["numx"] + 2 and any(
                         g["numx"] < h["x"] <= sg["x0"] + 15 and h["ymin"] - 80 <= sg["top"] <= h["ymax"] + 20
                         for h in cols_def))
                     and not (v2 and label and sg["x0"] > g["numx1"] + 8)]
            if cands:
                return max(cands, key=lambda i: cols_def[i]["x"])
        if v2 and label and any(g["x"] <= sg["x0"] + 15 and g["ymin"] - 80 <= sg["top"] <= g["ymax"] + 20
                                for g in cols_def):
            return None  # teks di kanan angka tabel (daftar pengurus/pemegang saham) -> blok sendiri
        cands = [i for i, g in enumerate(cols_def) if g["x"] <= sg["x0"] + 15] or [0]
        return max(cands, key=lambda i: cols_def[i]["x"])

    order = sorted(range(len(cols_def)), key=lambda i: (cols_def[i]["x"], cols_def[i]["ymin"]))
    cols = {i: [] for i in order + [None]}
    label_col = {}
    for sg in segs:
        if not is_num(sg):
            label_col[id(sg)] = col_of(sg, label=True)
    num_col, cat_hdr = {}, []
    for sg in segs:
        if is_num(sg):
            # angka ikut kolom LABA-nya: label terdekat di kiri pada baris yang sama
            left = [o for o in same_line(sg) if not is_num(o) and o["x1"] <= sg["x0"] + 1
                    and re.search(r"[A-Za-z]{2,}", o["text"])]
            nxt = [o for o in same_line(sg) if not is_num(o) and 0 <= o["x0"] - sg["x1"] < 6]
            if v2 and sg["text"] == "-" and nxt and label_col.get(id(nxt[0]), 0) is None:
                num_col[id(sg)] = None  # '- PT Panin Financial' : tanda daftar, bukan angka nol
            elif left:
                num_col[id(sg)] = label_col[id(max(left, key=lambda o: o["x1"]))]
            else:
                num_col[id(sg)] = col_of(sg)
            cols[num_col[id(sg)]].append(sg)
        elif v2 and all(t.lower() in _CAT_WORDS for t in sg["text"].split()) or v2 and re.fullmatch(
                r"(\d{1,2}\s+)?[A-Za-z]{3,9}\.?\s+\d{4}", sg["text"].strip()):
            # 'L DPK KL D M JUMLAH' / '31 DES 2025' (header tabel lebar): ikut kolom angka tepat di bawahnya
            cat_hdr.append(sg)
        else:
            cols[label_col[id(sg)]].append(sg)
    nums = [o for o in segs if is_num(o)]
    placed = []  # (kolom, top) header kolektibilitas yang dipindah
    for date_pass in (False, True):
        for sg in cat_hdr:
            is_date = not all(t.lower() in _CAT_WORDS for t in sg["text"].split())
            if is_date != date_pass:
                continue
            below = [o for o in nums if abs(o["x0"] - sg["x0"]) < 15 and 0 < o["top"] - sg["top"] < 40]
            ci = num_col[id(min(below, key=lambda o: o["top"]))] if below else None
            # tanggal hanya ikut kalau tepat di atas header kolektibilitas kolom itu (tabel kualitas aset)
            if ci is not None and (not is_date or any(c == ci and 0 < t - sg["top"] < 30 for c, t in placed)):
                cols[ci].append(sg)
                if not is_date:
                    placed.append((ci, sg["top"]))
            else:
                cols[label_col[id(sg)]].append(sg)
    cols = [cols[i] for i in order] + ([cols[None]] if cols[None] else [])

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
    best = new if _blocks_quality(new) > _blocks_quality(old) else old
    # varian 2: tabel berdampingan yang baris pertamanya beda tinggi, header kolektibilitas lebar,
    # daftar pengurus di samping tabel (Panin) -> dipakai hanya kalau jelas lebih baik
    v2 = _layout_blocks(page, v2=True)
    if v2 is not None and _blocks_quality(v2) > _blocks_quality(best) + 3:
        return v2
    return best


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
        line = re.sub(r"(?<=[\d)])[/!'\"]+(?=\s|$)", " ", line)  # '(8,326,874)/' -> garis tabel terbaca '/'
        line = re.sub(r"(\(\d[\d.,]*\d)\s*$", r"\1)", line)  # '(4,583,986' di ujung baris -> kurung tutup hilang
        line = re.sub(r"(\d[.,]) (\d{3})(?!\d)", r"\1\2", line)  # '1.379, 647' -> '1.379,647'
        # '27,981 308' -> '27,981,308' (pemisah ribuan terbaca spasi)
        line = re.sub(r"(?<![\w.,])(\d{1,3}(?:[.,]\d{3})+) (\d{3})(?![\d.,])", r"\1,\2", line)
        # '47 778,404' -> '47,778,404'
        line = re.sub(r"(?<![\w.,])(\d{1,3}) (\d{3}(?:[.,]\d{3})+)(?![\d.,])", r"\1,\2", line)
        line = re.sub(r"(?<=\d)\),(?=\s|$)", ")", line)  # '(344,729),' -> koma nyasar setelah kurung
        # pemisah ribuan campur ('2,462.058') -> semuanya ribuan
        line = re.sub(r"(?<![\d.,])(\d{1,3})((?:[.,]\d{3})+)(?![\d.,])",
                      lambda m: m.group(0) if len(set(re.findall(r"[.,]", m.group(2)))) < 2 and not
                      (m.group(2).count(",") == 1 and m.group(2).count(".") == 1)
                      else m.group(1) + re.sub(r"[.,]", ".", m.group(2)), line)
        line = re.sub(r"^I(?=(NET|TOTAL|PROFIT)\b)", "", line)  # garis tabel '|' terbaca 'I'
        # '(8,451)' terbaca '18,451)' -> kurung buka terbaca angka 1
        line = re.sub(r"(?<![\w.,(])1(\d{1,3}(?:[.,]\d{3})+)\)", r"(\1)", line)
        # kurung nyasar: '2,973,145)' tanpa '(' -> '2,973,145' ; '(Securities' -> 'Securities'
        line = re.sub(r"(?<![(\d.,])(\d[\d.,]*\d)\)", r"\1", line)
        line = re.sub(r"\((?=[A-Za-z]{3,}\b)(?![^()]*\))", "", line)
        out.append(re.sub(r"\s{2,}", " ", line).strip())
    return "\n".join(out)


_CAT_FUZZY = {"current": "L", "lancar": "L", "l": "L", "special": "DPK", "dpk": "DPK", "substandard": "KL",
              "kl": "KL", "doubtful": "D", "diragukan": "D", "d": "D", "loss": "M", "macet": "M", "m": "M",
              "total": "JUMLAH", "jumlah": "JUMLAH"}


def _cat_of(word):
    import difflib

    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return None
    if w in _CAT_FUZZY:
        return _CAT_FUZZY[w]
    if len(w) >= 6:
        hit = difflib.get_close_matches(w, [k for k in _CAT_FUZZY if len(k) >= 6], n=1, cutoff=0.7)
        return _CAT_FUZZY[hit[0]] if hit else None
    return None


def _ocr_positional_table(img, lang):
    """OCR tabel kolektibilitas dengan posisi kata: angka ditempatkan ke kolom header terdekat dan sel
    kosong diisi '-' (OCR biasa membuang tanda '-' sehingga kolom bergeser). None kalau tidak ada header
    kolektibilitas di gambar ini."""
    import pytesseract

    d = pytesseract.image_to_data(img, lang=lang, config="--psm 6", output_type=pytesseract.Output.DICT)
    lines = {}
    for i, w in enumerate(d["text"]):
        if not w.strip():
            continue
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        w = re.sub(r"^[|\[\]{}!]+|[|\[\]{}!]+$", "", w.strip())  # garis tabel menempel di angka
        if not w:
            continue
        lines.setdefault(key, []).append((d["left"][i], d["left"][i] + d["width"][i], d["top"][i], w))
    ordered = sorted(lines.values(), key=lambda ws: min(t for _, _, t, _ in ws))
    centers, cats, out = None, None, []
    for ws in ordered:
        ws.sort()
        cw = [(x0, x1, _cat_of(w)) for x0, x1, _, w in ws]
        found = [(x0 + x1) / 2 for x0, x1, c in cw if c]
        if len(found) >= 6 and len(found) >= 0.6 * len(ws):
            centers = found
            cats = [c for _, _, c in cw if c]
            out.append(" ".join(cats))
            continue
        line = clean_ocr_text(" ".join(w for _, _, _, w in ws))
        if not centers:
            out.append(line)
            continue
        nums = [((x0 + x1) / 2, w) for x0, x1, _, w in ws if re.fullmatch(r"\(?-?[\d.,]+\)?[,.]?", w)
                and re.search(r"\d", w) and x1 > min(centers) - 0.6 * (centers[1] - centers[0])]
        label_ws = [w for x0, x1, _, w in ws if x1 < min(centers) - 0.4 * (centers[1] - centers[0])]
        if not nums and not label_ws:
            continue
        step = (centers[-1] - centers[0]) / max(1, len(centers) - 1)
        bounds = [(centers[k] + centers[k + 1]) / 2 for k in range(len(centers) - 1)]
        slots = ["-"] * len(centers)
        ok = True
        for x, w in nums:
            if x < centers[0] - step or x > centers[-1] + step:
                ok = False
                break
            j = sum(1 for bnd in bounds if x > bnd)
            if slots[j] != "-":
                ok = False  # dua angka di satu kolom -> posisi tidak bisa dipercaya
                break
            w = w.rstrip(",.")
            if w.startswith("("):  # tabel kolektibilitas tidak punya angka negatif: '(' = angka 1 terbaca salah
                w = "1" + w[1:].rstrip(")")
            slots[j] = w
        if not ok or not nums:
            out.append(line)
            continue
        out.append(clean_ocr_text(" ".join(label_ws) + " " + " ".join(slots)))
    if not centers:
        return None
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
            if re.search(r"(Current|Lancar|L)\s+(Special|DPK)", txt, re.I):
                pos = _ocr_positional_table(img, lang)
                if pos:
                    texts.append(pos)
                    continue
            texts.append(clean_ocr_text(txt))
        except Exception:
            continue
    return texts


def _is_vector_text_page(page) -> bool:
    """Halaman koran yang hurufnya digambar sebagai vektor (tidak ada teks, ribuan kurva/kotak)."""
    try:
        return len(page.chars) < 20 and len(page.curves) + len(page.rects) > 500
    except Exception:  # pragma: no cover
        return False


def _vector_page_regions(page):
    """Bagi halaman jadi potongan per tabel memakai bar judul tabel (kotak berwarna):
    potongan mulai sedikit di atas bar (judul tabel) sampai sebelum bar berikutnya yang menimpa
    rentang x-nya. Urutan: per kolom (kiri->kanan), atas->bawah."""
    W, H = page.width, page.height
    # hanya bar selebar tabel (bar kecil = judul sub-kolom angka, bukan batas tabel)
    bars = [(r["x0"], r["top"], r["x1"]) for r in page.rects if 150 < r["width"] < 0.6 * W and r["height"] < 40]
    bars = [b for b in bars if not any(o != b and abs(o[1] - b[1]) < 3 and o[0] <= b[0] + 1 and o[2] >= b[2] - 1
                                       and (o[2] - o[0]) > (b[2] - b[0]) + 2 for o in bars)]
    if not bars:
        return [(0, 0, W, H)]
    # bar berdampingan di ketinggian sama (judul kolom angka satu tabel) -> satu bar
    merged = []
    for b in sorted(bars, key=lambda b: (round(b[1]), b[0])):
        if merged and abs(merged[-1][1] - b[1]) < 3 and -1 <= b[0] - merged[-1][2] < 1.5:
            merged[-1] = (merged[-1][0], merged[-1][1], max(merged[-1][2], b[2]))
        else:
            merged.append(b)
    bars = merged
    pad = 45
    # kelompokkan bar per rentang x (satu kolom tabel)
    clusters = []
    for b in sorted(bars, key=lambda b: (b[1], b[0])):
        for c in clusters:
            if abs(c[0] - b[0]) < 15 and abs(c[1] - b[2]) < 15:
                c[2].append(b[1])
                break
        else:
            clusters.append([b[0], b[2], [b[1]]])

    def overlap(c, d):
        return min(c[1], d[1]) - max(c[0], d[0]) > 0.5 * min(c[1] - c[0], d[1] - d[0])

    def internal(d, c):
        """d = bar sub-kolom DI DALAM tabel c (lebih sempit, muncul setelah judul c)."""
        return (d is not c and d[0] >= c[0] - 6 and d[1] <= c[1] + 6 and (d[1] - d[0]) < (c[1] - c[0]) - 10
                and min(d[2]) > min(c[2]))

    regions = []
    for c in clusters:
        if any(internal(c, h) for h in clusters):
            continue
        events = sorted([(t, id(c)) for t in c[2]] +
                        [(t, id(d)) for d in clusters if d is not c and overlap(c, d) and not internal(d, c)
                         for t in d[2]])
        start = None
        for k, (t, owner) in enumerate(events):
            if owner == id(c) and start is None:
                start = max(0, t - pad) if k == 0 or events[k - 1][1] != id(c) else t
            elif owner != id(c) and start is not None and t > start:
                regions.append((c[0], start, c[1], max(start + 1, t - pad)))
                start = None
        if start is not None:
            regions.append((c[0], start, c[1], H))
    regions = [r for r in regions if r[3] - r[1] >= 8]
    cols = sorted({round(r[0] / 30) for r in regions})
    return sorted(regions, key=lambda r: (cols.index(round(r[0] / 30)), r[1]))


def _ocr_lines(img, lang):
    """OCR -> [(top, teks)] per baris (posisi y dalam piksel)."""
    import pytesseract

    d = pytesseract.image_to_data(img, lang=lang, config="--psm 6", output_type=pytesseract.Output.DICT)
    lines = {}
    for i, w in enumerate(d["text"]):
        if (w or "").strip():
            key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
            lines.setdefault(key, []).append((d["left"][i], d["top"][i], d["height"][i], w))
    out = []
    for ws in lines.values():
        ws.sort()
        out.append((min(t for _, t, _, _ in ws), max(h for _, _, h, _ in ws), " ".join(w for *_, w in ws)))
    return sorted(out)


def _is_numbers_only(text):
    toks = text.split()
    return bool(toks) and all(re.fullmatch(r"[(\-]?[\d.,]+\)?%?|-|=|:", t) for t in toks) and re.search(r"\d", text)


def _merge_label_number_crops(img, a_box, b_box, lang):
    """Tabel lebar yang terpotong dua (label di potongan kiri, angka saja di potongan kanan pada
    ketinggian yang sama): bagian itu di-OCR ulang selebar tabel. Return (teks_a, teks_b) atau None."""
    import pytesseract

    la, lb = _ocr_lines(img.crop(a_box), lang), _ocr_lines(img.crop(b_box), lang)
    ys = []
    for top, h, text in la:
        if re.search(r"\d[\d.,]{3,}", text):
            continue
        y = top + a_box[1]
        if any(abs((tb + b_box[1]) - y) <= max(h, hb) and _is_numbers_only(tx) for tb, hb, tx in lb):
            ys.append((y, h))
    if len(ys) < 3:
        return None
    y0 = max(min(y for y, _ in ys) - 2 * ys[0][1], a_box[1])
    # ujung tabel: sampai baris pasangan terakhir + sedikit
    y1 = min(max(y + h for y, h in ys) + 3 * ys[-1][1], a_box[3])
    union = (a_box[0], int(y0), b_box[2], int(y1))
    mid = pytesseract.image_to_string(img.crop(union), lang=lang, config="--psm 6")

    def outside(lines, box):
        return "\n".join(t for top, _, t in lines if not (y0 - 2 <= top + box[1] <= y1))

    top_a = "\n".join(t for top, _, t in la if top + a_box[1] < y0 - 2)
    rest_a = "\n".join(t for top, _, t in la if top + a_box[1] > y1)
    return "\n".join(x for x in (top_a, mid, rest_a) if x), outside(lb, b_box)


def _ocr_vector_page(page, lang="ind+eng", dpi=300):
    """OCR halaman vektor: render sekali, binarisasi (teks putih di bar berwarna dibalik jadi hitam),
    lalu OCR tiap potongan tabel."""
    import numpy as np
    import pytesseract
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    gray = np.array(page.to_image(resolution=dpi).original.convert("L")).astype(np.uint8)
    sc = dpi / 72.0
    # dua versi gambar: abu-abu (baik untuk baris yang diarsir) & hitam-putih (baik untuk teks berwarna);
    # di keduanya teks putih di bar gelap dibalik jadi hitam. Tiap potongan dipilih versi yang
    # keyakinan OCR angkanya paling tinggi.
    out_g = gray.copy()
    out_b = np.where(gray < 200, 0, 255).astype(np.uint8)
    for r in page.rects:
        if r["width"] <= 20 or r["height"] <= 4:
            continue
        X0, T, X1, B = int(r["x0"] * sc), int(r["top"] * sc), int(r["x1"] * sc), int(r["bottom"] * sc)
        reg = gray[T:B, X0:X1]
        if reg.size and np.median(reg) < 200:
            inv = np.where(reg > 200, 0, 255)
            out_g[T:B, X0:X1] = inv
            out_b[T:B, X0:X1] = inv
    img = Image.fromarray(out_g)
    img_b = Image.fromarray(out_b)
    texts = []
    regions = _vector_page_regions(page)
    boxes = [(max(0, int(x0 * sc) - 8), max(0, int(top * sc)), min(img.size[0], int(x1 * sc) + 8),
              min(img.size[1], int(bottom * sc))) for x0, top, x1, bottom in regions]
    override = {}
    for ia, a in enumerate(boxes):
        for ib, b in enumerate(boxes):
            # dua potongan bersebelahan, tinggi sama -> mungkin satu tabel lebar terbelah (label | angka)
            if ia != ib and 0 <= b[0] - a[2] < 40 and abs(a[1] - b[1]) < 30 and abs(a[3] - b[3]) < 30 \
                    and ia not in override and ib not in override:
                try:
                    m = _merge_label_number_crops(img, a, b, lang)
                except Exception:
                    m = None
                if m:
                    override[ia], override[ib] = clean_ocr_text(m[0]), clean_ocr_text(m[1])
    for k, box in enumerate(boxes):
        if k in override:
            texts.append(override[k])
            continue
        if box[2] - box[0] < 20 or box[3] - box[1] < 20:
            continue
        crop = img_b.crop(box)
        try:
            txt = pytesseract.image_to_string(crop, lang=lang, config="--psm 6")
        except pytesseract.TesseractError:
            txt = pytesseract.image_to_string(crop, config="--psm 6")
        if re.search(r"\b(L|Lancar|Current)\s+(DPK|Special)\b", txt, re.I):
            pos = _ocr_positional_table(crop, lang)  # tabel kolektibilitas: sel kosong dipertahankan
            if pos:
                texts.append(pos)
                continue
        texts.append(clean_ocr_text(txt))
    return texts


def parse_pdf(file_bytes: bytes, allow_ocr: bool = True):
    """-> (rows, full_text)"""
    import pdfplumber

    builder = _RowBuilder()
    texts = []
    use_ocr = allow_ocr and ocr_available()
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            try:
                head = "\n".join((page.extract_text() or "").splitlines()[:3])
            except Exception:  # pragma: no cover - halaman rusak
                head = ""
            builder.set_page(pno, head)
            page = _drop_ghost_spaces(page)
            blocks = _page_blocks(page)
            if use_ocr and sum(_count_numeric_lines(b) for b in blocks) < 3 and _is_vector_text_page(page):
                ocr_blocks = _ocr_vector_page(page)
                if sum(_count_numeric_lines(b) for b in ocr_blocks) >= 3:
                    blocks = ocr_blocks
                    builder.ocr_used = True
            elif use_ocr and sum(_count_numeric_lines(b) for b in blocks) < 3 and page.images:
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
    from .ojk import is_ojk_excel, parse_ojk_excel

    if is_ojk_excel(file_bytes):
        return parse_ojk_excel(file_bytes)  # export portal OJK (cfs.ojk.go.id)
    return parse_excel(file_bytes)
