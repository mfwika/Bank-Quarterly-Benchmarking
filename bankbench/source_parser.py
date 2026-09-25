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


def _combine_header(dates, ents, n_values=None):
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
        self.ocr_used = False

    def header_line(self, line) -> bool:
        d = parse_date_header(line)
        if d:
            self.dates = d
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
        self.section = section
        self.stack = []
        self.pending = None
        self.last_letter = None
        self.dates = None
        self.ents = None

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
        self.rows.append(SourceRow(len(self.rows), label, list(values), self.section, parent, self.page,
                                   _combine_header(self.dates, self.ents, len(values))))


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
        if parse_date_header(raw) or parse_entity_header(raw):
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
    """Beberapa PDF (mis. BCA) menaruh karakter spasi yang MENUMPUK di posisi digit
    pertama, sehingga '25.275.044' terbaca '2 5.275.044'. Spasi yang posisinya sama
    dengan karakter lain dibuang dulu."""
    try:
        solid = {(round(c["top"]), round(c["x0"])) for c in page.chars if c["text"].strip()}
    except Exception:
        return page
    if not solid:
        return page

    def keep(obj):
        if obj.get("object_type") != "char" or obj.get("text") != " ":
            return True
        return (round(obj["top"]), round(obj["x0"])) not in solid

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


def _page_blocks(page):
    """Laporan publikasi di koran/web sering multi-kolom (Neraca | Laba Rugi | ...).
    Kalau ada 'selokan' vertikal yang jelas, halaman dipecah per kolom supaya baris
    dari kolom yang berbeda tidak tercampur."""
    try:
        return _split_columns(page, 0, page.width)
    except Exception:
        return [page.extract_text() or ""]


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
