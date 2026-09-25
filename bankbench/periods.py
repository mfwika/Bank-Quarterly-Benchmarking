import re
from collections import Counter
from datetime import date

MONTHS = {
    "jan": 1, "januari": 1, "january": 1,
    "feb": 2, "februari": 2, "february": 2, "pebruari": 2,
    "mar": 3, "maret": 3, "march": 3,
    "apr": 4, "april": 4,
    "mei": 5, "may": 5,
    "jun": 6, "juni": 6, "june": 6,
    "jul": 7, "juli": 7, "july": 7,
    "agu": 8, "agt": 8, "ags": 8, "aug": 8, "agustus": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "okt": 10, "oct": 10, "oktober": 10, "october": 10,
    "nov": 11, "nopember": 11, "november": 11,
    "des": 12, "dec": 12, "desember": 12, "december": 12,
}
EN_ABBR = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
           7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
QUARTER_END_DAY = {3: 31, 6: 30, 9: 30, 12: 31}

PERIOD_PATTERN = re.compile(
    r"(Jan|Feb|Mar|Apr|Mei|May|Jun|Jul|Agu|Aug|Sep|Okt|Oct|Nov|Des|Dec)[a-z]*\.?\s*'?\d{2,4}",
    re.IGNORECASE,
)


def looks_like_period(value) -> bool:
    if value is None or not isinstance(value, str):
        return False
    s = value.strip()
    return bool(PERIOD_PATTERN.search(s)) and len(s) <= 15


def parse_period_label(text):
    """'Sep 25' / 'Mar 2009' / "Dec'24" -> (month, full_year) atau None."""
    if text is None:
        return None
    m = re.match(r"^\s*([A-Za-z]+)\.?\s*'?\s*(\d{2,4})\s*$", str(text).strip())
    if not m:
        return None
    mon = MONTHS.get(m.group(1).lower()) or MONTHS.get(m.group(1).lower()[:3])
    if not mon:
        return None
    yr = int(m.group(2))
    if yr < 100:
        yr += 2000
    return mon, yr


def format_period_label(month: int, year: int, like: str | None = None) -> str:
    """Ikuti format label yang sudah dipakai template (default 'Sep 25')."""
    four = False
    if like:
        m = re.search(r"(\d{2,4})\s*$", str(like))
        four = bool(m and len(m.group(1)) == 4)
    return f"{EN_ABBR[month]} {year if four else str(year)[-2:]}"


def quarter_end(month: int, year: int) -> date:
    return date(year, month, QUARTER_END_DAY.get(month, 30))


_DATE_IN_TEXT = re.compile(
    r"\b(\d{1,2})\s+(Januari|January|Februari|Pebruari|February|Maret|March|April|Mei|May|Juni|June|"
    r"Juli|July|Agustus|August|September|Oktober|October|November|Nopember|Desember|December)\s+(\d{4})\b",
    re.IGNORECASE,
)


def detect_report_period(text: str):
    """Tebak periode laporan dari teks: tanggal akhir kuartal yang PALING BARU &
    sering muncul (mis. '30 September 2025'). Return (month, year) atau None."""
    if not text:
        return None
    counts = Counter()
    for d, mon_name, yr in _DATE_IN_TEXT.findall(text):
        mon = MONTHS.get(mon_name.lower())
        if mon in QUARTER_END_DAY and int(d) in (30, 31):
            counts[(mon, int(yr))] += 1
    if not counts:
        return None
    latest = max(counts, key=lambda k: (k[1], k[0]))
    return latest
