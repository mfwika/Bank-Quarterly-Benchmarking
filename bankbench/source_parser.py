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
    ("CAP", re.compile(r"PENYEDIAAN MODAL MINIMUM|KPMM|CAPITAL ADEQUACY|PERHITUNGAN MODAL|PERMODALAN|KOMPONEN MODAL")),
    ("COMMIT", re.compile(r"KOMITMEN|KONTI[NJ]+ENSI|KONTIGENSI")),
    ("IS", re.compile(r"LABA\s*\(?\s*RUGI|LABA\s*/\s*RUGI|PENGHASILAN KOMPREHENSIF|INCOME STATEMENT|PROFIT OR LOSS")),
    ("BS", re.compile(r"POSISI KEUANGAN|NERACA|BALANCE SHEET|FINANCIAL POSITION")),
    ("OTHER", re.compile(
        r"KUALITAS ASET|RASIO KEUANGAN|TRANSAKSI SPOT|CADANGAN PENYISIHAN|LIKUIDITAS|PENGURUS|PEMEGANG SAHAM"
        r"|ARUS KAS|PERUBAHAN EKUITAS|LEVERAGE|LIQUIDITY COVERAGE|NET STABLE|EKSPOSUR|MANAJEMEN RISIKO"
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

    def value_at(self, i):
        return self.values[i] if 0 <= i < len(self.values) else None


def _heading_section(text: str):
    """Kalau baris ini judul laporan -> kode seksinya, selain itu None."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 6:
        return None
    if sum(1 for c in letters if c.isupper()) / len(letters) < 0.75:
        return None
    u = text.upper()
    for key, pat in SECTION_PATTERNS:
        if pat.search(u):
            return key
    return None


class _RowBuilder:
    """Mengubah aliran baris (label + angka) menjadi SourceRow lengkap dengan
    seksi & induk akun."""

    def __init__(self):
        self.rows: list[SourceRow] = []
        self.section = "?"
        self.stack = []  # (level, label)
        self.pending = None  # label tanpa angka (induk / label yang terpotong)
        self.last_letter = None
        self.page = None

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
        self.section = section
        self.stack = []
        self.pending = None
        self.last_letter = None

    def text_only(self, text, token=None):
        """Baris tanpa angka: judul seksi, induk akun, atau potongan label."""
        sec = _heading_section(text)
        if sec:
            self.heading(sec)
            return
        label = strip_leading_enumerators(text)
        if not re.search(r"[A-Za-z]{2,}", label):
            return
        if self.pending and not token and label[:1].islower():
            self.pending = (self.pending[0], self.pending[1] + " " + label)
            return
        self.pending = (token, label)

    def add(self, label, values, token=None):
        label = strip_leading_enumerators(label).strip(" .:")
        # label terpotong: 'Keuntungan (kerugian) dari ...' + baris berikut 'nilai wajar ... 1.234'
        if self.pending:
            p_token, p_label = self.pending
            if not token and label[:1].islower():
                label = f"{p_label} {label}"
                token = p_token
            else:
                self._push(self._level(p_token), p_label)
            self.pending = None
        if not re.search(r"[A-Za-z]{2,}", label):
            return
        parent = self._push(self._level(token), label)
        self.rows.append(SourceRow(len(self.rows), label, list(values), self.section, parent, self.page))


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


def _feed_text(builder: _RowBuilder, text: str):
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        token, label, values = split_label_values(line)
        if not values:
            if label:
                builder.text_only(label, token)
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


def _page_blocks(page):
    """Laporan publikasi di koran/web sering 2 kolom (Neraca di kiri, Laba Rugi
    di kanan). Kalau ada 'selokan' vertikal yang jelas, halaman dipecah jadi 2
    supaya baris kiri & kanan tidak tercampur."""
    full_text = page.extract_text() or ""
    try:
        words = page.extract_words()
    except Exception:
        return [full_text]
    if len(words) < 40:
        return [full_text]
    width = int(page.width) + 2
    cover = [0] * width
    for w in words:
        for x in range(max(0, int(w["x0"])), min(width, int(w["x1"]) + 1)):
            cover[x] += 1
    n_lines = max(1, len({round(w["top"]) for w in words}))
    limit = max(2, int(0.03 * n_lines))
    lo, hi = int(page.width * 0.3), int(page.width * 0.7)
    best, run_start = None, None
    for x in range(lo, hi + 1):
        if cover[x] <= limit:
            run_start = x if run_start is None else run_start
            if best is None or (x - run_start) > (best[1] - best[0]):
                best = (run_start, x)
        else:
            run_start = None
    if not best or best[1] - best[0] < 6:
        return [full_text]
    split_x = (best[0] + best[1]) / 2
    try:
        left = page.crop((0, 0, split_x, page.height)).extract_text() or ""
        right = page.crop((split_x, 0, page.width, page.height)).extract_text() or ""
    except Exception:
        return [full_text]
    if _count_numeric_lines(left) >= 5 and _count_numeric_lines(right) >= 5:
        return [left, right]
    return [full_text]


def parse_pdf(file_bytes: bytes):
    """-> (rows, full_text)"""
    import pdfplumber

    builder = _RowBuilder()
    texts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            builder.set_page(pno)
            blocks = _page_blocks(page)
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
