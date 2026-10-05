"""MODE STRICT: isi template dengan MENIRU POLA periode acuan.

Aturan periode acuan (sesuai cara kerja analis):
  - Neraca (BS)                          -> Desember tahun sebelumnya
  - Laba Rugi (IS), KPMM (CAP), NPL, rasio -> periode yang sama tahun lalu (YoY)
Kolom pembanding di laporan publikasi memang selalu periode-periode itu, jadi:

  1. Ambil nilai template di periode acuan (h).
  2. Cari 'resep' di laporan: satu akun, atau jumlah 2-3 akun, yang angka
     PEMBANDING-nya (periode acuan, entitas yang sama) persis = h.
  3. Terapkan resep yang sama ke angka PERIODE BERJALAN.
  4. Kalau resep tidak ketemu -> baris DIKOSONGKAN + ditandai (tidak ditebak).
     Tebakan berdasarkan nama akun hanya ditampilkan sebagai saran.

Entitas: BS/IS/CAP selalu Konsolidasian (kecuali judul seksi template menyebut
'Bank only'), NPL & rasio mengikuti entitas yang cocok di periode acuan.
"""
import re
from collections import defaultdict
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from .aliases import lookup
from .matcher import MIN_ANCHOR_ABS, Layout, Matcher, MatchResult, _close, _is_expense
from .text import clean_label, similarity

TOL = 1.0


def reference_period(section: str, month: int, year: int):
    """Periode acuan pola untuk seksi tsb."""
    if section == "BS":
        return (12, year - 1)
    return (month, year - 1)


@dataclass
class Recipe:
    parts: list  # [(SourceRow, sign)]
    kind: str  # 'single' | 'sum'
    ref_value: float
    notes: list = field(default_factory=list)


# Kebiasaan analis yang terlihat di banyak bank (dipakai kalau pola angka tidak tersedia):
# baris template -> akun laporan tambahan yang ikut dijumlahkan.
SEED_CONVENTIONS = {
    "BS": {"aset lainnya": ["aset keuangan lainnya", "other financial assets", "other financial asset"],
           "liabilitas lainnya": ["uang elektronik", "liabilitas kontrak asuransi", "electronic money",
                                  "insurance contract liabilities"],
           "tahun tahun lalu": ["dividen yang dibayarkan", "dividends paid", "dividend paid", "payable dividend"],
           "pinjaman yang diberikan dan piutang": ["piutang pembiayaan konsumen", "finance receivables",
                                                   "consumer financing receivables"],
           "pendapatan kerugian komprehensif lainnya": ["loss"]},
    "IS": {"pendapatan lainnya": ["pendapatan asuransi", "insurance services income", "insurance income"],
           "beban lainnya": ["beban asuransi", "insurance services expense", "insurance expense"]},
}
FALLBACK_METHODS = ("Memori pola", "Nama akun", "Penyeimbang", "Turunan total")


class StrictMatcher(Matcher):
    """Pencocokan berbasis pola angka periode acuan, dengan cadangan pengenalan akun."""

    def __init__(self, model, source_rows, target_col, aliases, period, entity_by_section=None, recipe_hints=None,
                 fallback=True, conventions=None):
        source_rows = _own_company_rows(model, source_rows)
        super().__init__(model, source_rows, target_col, aliases, period=period)
        self.fallback = fallback
        self.conventions = {sec: dict(d) for sec, d in SEED_CONVENTIONS.items()}
        for sec, d in (conventions or {}).items():
            for k, v in d.items():
                bucket = self.conventions.setdefault(sec, {}).setdefault(k, [])
                bucket.extend(x for x in v if x not in bucket)
        self.source_all = list(source_rows)
        # row -> [label akun laporan] resep yang dipakai sebelumnya (memori pola)
        self.recipe_hints = dict(getattr(model, "recipe_hints", None) or {})
        self.recipe_hints.update(recipe_hints or {})
        self.month, self.year = period
        self.ref_period = {sec: reference_period(sec, self.month, self.year) for sec in ("BS", "IS", "CAP")}
        self.ref_cols = {sec: model.find_period_col(*p) for sec, p in self.ref_period.items()}
        self.entity = entity_by_section or {sec: _section_entity(model, sec) for sec in ("BS", "IS", "CAP")}
        self.scale = 1.0
        self.layout = Layout(0, None, 0, 1.0, 0, {}, "KONS", True)

    # ------------------------------------------------------------ kolom angka
    def _index(self, sr, period, entity, role):
        """Posisi angka untuk (periode, entitas). role: 'cur' / 'ref' (fallback posisi
        kalau tabel tidak punya header yang terbaca)."""
        meta = self._col_meta(sr)
        if meta and any(p for p, _ in meta):
            hits = [i for i, (p, _) in enumerate(meta) if p == period]
            if not hits:
                return None
            ents = {e for _, e in meta if e}
            if entity and entity in ents:
                hits = [i for i in hits if meta[i][1] == entity]
            return hits[0] if hits else None
        n = len(sr.values)
        if n == 4:
            if self._date_major(sr.section):  # [kini IND, kini KONS, lalu IND, lalu KONS]
                return (0 if entity == "IND" else 1) + (0 if role == "cur" else 2)
            base = 0 if entity == "IND" else 2
            return base + (0 if role == "cur" else 1)
        if n == 2:
            return 0 if role == "cur" else 1
        return None

    def _date_major(self, section):
        """Tabel tanpa header terbaca (mis. OCR): urutan kolom ditebak dengan mencocokkan angka ke
        Neraca Konsolidasian periode berjalan (mis. 'Laba tahun berjalan' muncul di Neraca & KPMM)."""
        cache = self.__dict__.setdefault("_date_major_cache", {})
        if section in cache:
            return cache[section]
        cache[section] = False
        if section == "BS":
            return False
        bs = set()
        for x in self.source_all:
            if x.section == "BS":
                v = self.cur_value(x, "BS")
                if v is not None and abs(v) >= 1000:
                    bs.add(round(abs(v)))
        rows = [x for x in self.source_all if x.section == section and len(x.values) == 4
                and not (self._col_meta(x) and any(p for p, _ in self._col_meta(x)))]
        hit1 = sum(1 for x in rows if round(abs(x.values[1])) in bs)
        hit2 = sum(1 for x in rows if round(abs(x.values[2])) in bs)
        cache[section] = hit1 >= 2 and hit1 > hit2
        return cache[section]

    def cur_value(self, sr, section=None):
        sec = section or sr.section
        i = self._index(sr, self.period, self.entity.get(sec, "KONS"), "cur")
        v = None if i is None else sr.value_at(i)
        return None if v is None else v * self.scale

    def ref_value(self, sr, section=None):
        sec = section or sr.section
        per = self.ref_period.get(sec)
        i = self._index(sr, per, self.entity.get(sec, "KONS"), "ref")
        v = None if i is None else sr.value_at(i)
        return None if v is None else v * self.scale

    # dipakai reconcile() & UI
    def current_value(self, sr):
        return self.cur_value(sr)

    def value_for(self, tr, sr, sign=None):
        v = self.cur_value(sr, tr.section)
        if v is None:
            return None, ["angka periode berjalan tidak ada di baris ini"]
        notes = []
        hist = [h for _, h in self.history(tr, 4) if h != 0]
        if v and len(hist) >= 2 and _is_expense(tr.label, sr.label):
            want = 1 if all(h > 0 for h in hist) else -1 if all(h < 0 for h in hist) else 0
            if want and (v > 0) != (want > 0):
                v, notes = -v, ["tanda disesuaikan ke konvensi template"]
        return v, notes

    # ------------------------------------------------------------ skala
    def _detect_scale(self):
        best = (0, 1.0)
        for scale in (1.0, 0.001, 1000.0):
            self.scale = scale
            n = 0
            for tr in self._value_rows:
                col = self.ref_cols.get(tr.section)
                h = tr.numeric(col) if col else None
                if h is None or abs(h) < MIN_ANCHOR_ABS:
                    continue
                if any((r := self.ref_value(s, tr.section)) is not None and _close(abs(r), abs(h))
                       for s in self._cands(tr)):
                    n += 1
            if n > best[0]:
                best = (n, scale)
        self.scale = best[1]
        return best

    # ------------------------------------------------------------ resep
    def _cands(self, tr):
        return [s for s in self.source if s.section == tr.section or s.section == "?"]

    def _support(self, tr, sr):
        """Dukungan nama (hanya untuk memecah seri / angka kecil)."""
        return max(self._label_score(tr, sr), self._alias_score(tr, sr))

    def find_recipe(self, tr, used):
        col = self.ref_cols.get(tr.section)
        if col is None:
            return None, "periode acuan belum ada di template"
        h = tr.numeric(col)
        if h is None:
            return None, f"kosong di periode acuan ({self.model.period_cols.get(col)})"
        cands = []
        for s in self._cands(tr):
            if s.idx in used:
                continue
            r = self.ref_value(s, tr.section)
            if r is not None:
                cands.append((s, -r if getattr(self, "_neg_flip", False) else r))

        # 0) memori resep (dipakai di periode sebelumnya): kalau jumlahnya tetap persis = h,
        #    pakai resep yang sama — termasuk akun yang di periode acuan kebetulan bernilai 0
        hint = self.recipe_hints.get(tr.row)
        if hint and len(hint) > 1:
            picked = []
            for lbl in hint:
                m = [(s, r) for s, r in cands if clean_label(s.label) == clean_label(lbl)
                     and s.idx not in {p.idx for p, _ in picked}]
                if not m:
                    picked = None
                    break
                m.sort(key=lambda x: self._pos_bonus(tr, x[0]), reverse=True)
                picked.append(m[0])
            if picked and _close(sum(r for _, r in picked), h):
                return Recipe([(s, 1) for s, _ in picked], "sum", h, ["resep sama dengan periode sebelumnya"]), None

        # 1) satu akun
        singles = [(s, 1 if (r >= 0) == (h >= 0) or r == 0 else -1) for s, r in cands if _close(abs(r), abs(h))]
        if h == 0 or abs(h) < 100:
            # angka nol/kecil sering kebetulan sama -> wajib didukung nama akun
            singles = [(s, sg) for s, sg in singles if self._support(tr, s) >= 75]
        if singles:
            if len(singles) > 1:
                singles.sort(key=lambda x: self._support(tr, x[0]) + self._pos_bonus(tr, x[0]), reverse=True)
            s, sg = singles[0]
            note = [] if len(singles) == 1 else [f"{len(singles)} akun punya angka sama, dipilih yang namanya paling cocok"]
            return Recipe([(s, sg)], "single", h, note), None
        if abs(h) < MIN_ANCHOR_ABS:
            return None, "tidak ada akun laporan dengan angka acuan yang sama"

        # 2) jumlah 2-3 akun (tanpa baris total/subtotal), minimal satu yang namanya mirip
        # baris beban (positif di template): pos laporan '(beban) ... bersih' yang negatif ikut dihitung
        expense = h > 0 and bool(re.match(r"\s*(beban|kerugian)", tr.label, re.I))
        sign_of = {s.idx: -1 for s, r in cands if (expense and r < 0) or getattr(self, "_neg_flip", False)}
        # 'Pendapatan (beban) ... bersih' boleh jadi komponen (mis. asuransi keuangan), tapi dikenai penalti subtotal
        pool = [(s, abs(r) if expense else r) for s, r in cands
                if r != 0 and (not _is_total(s.label) or _is_subtotalish(s.label)) and not _is_grand_total(s.label)
                and abs(r) <= 3 * abs(h) + 1]
        pool = pool[:120]
        by_val = defaultdict(list)
        for i, (s, r) in enumerate(pool):
            by_val[round(r)].append(i)
        def score(combos):
            out = []
            for c in combos:
                sups = [self._support(tr, pool[i][0]) for i in c]
                parents = {clean_label(pool[i][0].parent or "") for i in c}
                if max(sups) < 60 and len(parents) == 1 and "" not in parents and len(combos) == 1:
                    # nama tidak mirip, tapi satu-satunya kombinasi & semua akun satu induk
                    # (mis. 'Selisih penilaian kembali' = Gains + Losses di bawah 'Other comprehensive income')
                    out.append((50.0 - 3 * len(c), c))
                    continue
                if max(sups) >= 60:
                    # utamakan kombinasi yang anggotanya bukan subtotal & lebih sedikit
                    pen = sum(8 for i in c if _is_subtotalish(pool[i][0].label))
                    pen += sum(6 for i in c if pool[i][0].idx in sign_of)  # tanda dibalik: pilihan terakhir
                    out.append((max(sups) + 0.2 * sum(sups) / len(sups) - pen - 3 * len(c), c))
            return out

        pairs = []
        for i in range(len(pool)):
            need = h - pool[i][1]
            for key in (round(need) - 1, round(need), round(need) + 1):
                for j in by_val.get(key, ()):
                    if j > i and _close(pool[i][1] + pool[j][1], h):
                        pairs.append((i, j))
        scored = score(pairs)
        if not scored:
            triples = []
            for i in range(len(pool)):
                for j in range(i + 1, len(pool)):
                    need = h - pool[i][1] - pool[j][1]
                    for key in (round(need) - 1, round(need), round(need) + 1):
                        for k in by_val.get(key, ()):
                            if k > j and _close(pool[i][1] + pool[j][1] + pool[k][1], h):
                                triples.append((i, j, k))
                if len(triples) > 200:
                    break
            scored = score(triples)
        if not scored:
            # 4 akun: pasangan + pasangan (meet-in-the-middle)
            pair_sums = defaultdict(list)
            n = len(pool)
            for i in range(n):
                for j in range(i + 1, n):
                    pair_sums[round(pool[i][1] + pool[j][1])].append((i, j))
            quads = set()
            for key, lst in pair_sums.items():
                for k2 in (round(h) - key - 1, round(h) - key, round(h) - key + 1):
                    for (i, j) in lst:
                        for (k, l) in pair_sums.get(k2, ()):
                            if len({i, j, k, l}) == 4 and _close(pool[i][1] + pool[j][1] + pool[k][1] + pool[l][1], h):
                                quads.add(tuple(sorted((i, j, k, l))))
                if len(quads) > 200:
                    break
            scored = score(sorted(quads))
        if not scored:
            if h < 0 and not getattr(self, "_neg_flip", False):
                # template menyimpan pengurang sebagai negatif, laporan menulis positif (Faktor Pengurang)
                self._neg_flip = True
                try:
                    rec, _ = self.find_recipe(tr, used)
                finally:
                    self._neg_flip = False
                if rec and rec.kind == "sum":
                    rec.notes = list(rec.notes) + ["pengurang ditulis positif di laporan -> tanda dibalik"]
                    return rec, None
            return None, "pola tidak ketemu di laporan (akun baru / angka pembanding di-restate?)"
        scored.sort(key=lambda x: x[0], reverse=True)
        if len(scored) > 1 and scored[0][0] - scored[1][0] < 5:
            close = [c for sc, c in scored if scored[0][0] - sc < 5]
            cur_sums = set()
            for c in close:
                vs = [self.cur_value(pool[i][0], tr.section) for i in c]
                cur_sums.add(None if any(v is None for v in vs) else
                             round(sum(sign_of.get(pool[i][0].idx, 1) * v for i, v in zip(c, vs))))
            if len(cur_sums) != 1 or None in cur_sums:
                return None, "beberapa kombinasi akun cocok dengan angka acuan — isi manual"
            # semua kombinasi memberi angka periode berjalan yang sama (mis. induk & anak bernilai sama)
        parts = [(pool[i][0], sign_of.get(pool[i][0].idx, 1)) for i in scored[0][1]]
        parts.sort(key=lambda p: -self._support(tr, p[0]))
        return Recipe(parts, "sum", h), None

    # ------------------------------------------------------------ cadangan (tanpa pola angka)
    def _ref_usable(self, section):
        """Kolom acuan dianggap ada kalau cukup banyak akun seksi ini terisi di sana."""
        col = self.ref_cols.get(section)
        if col is None:
            return False
        cache = self.__dict__.setdefault("_ref_usable_cache", {})
        if section not in cache:
            rows = [tr for tr in self._value_rows if tr.section == section and tr.row not in self._formula_rows]
            usual = [tr for tr in rows if self.usually_filled(tr)] or rows
            filled = sum(1 for tr in usual if tr.numeric(col) is not None)
            cache[section] = bool(usual) and filled >= max(1, 0.25 * len(usual))
        return cache[section]

    def _fallback(self, recipes, reasons, used):
        """Baris yang tidak punya pola angka tetap dikenali akunnya:
        1. memori pola (resep bank ini dari periode sebelumnya)
        2. nama akun / kamus padanan (+ kebiasaan penjumlahan umum, + jumlah sub-akun)
        3. penyeimbang total Neraca
        Semua ditandai 'CEK'."""
        out = {}
        used = set(used)
        todo = []
        for tr in self._value_rows:
            if tr.row in self._formula_rows or tr.row in recipes or tr.row in self._redirected_parents:
                continue
            col = self.ref_cols.get(tr.section)
            ref_h = tr.numeric(col) if col else None
            if self._ref_usable(tr.section):
                if ref_h is None:
                    continue  # kosong di periode acuan -> memang tidak diisi (konvensi analis)
            elif not self.usually_filled(tr):
                continue
            todo.append(tr)
        todo.sort(key=lambda tr: -abs(self.last_value(tr) or 0))

        def value_of(tr, parts):
            vals = []
            for sr in parts:
                v = self._fb_value(tr, sr)
                if v is None:
                    return None
                vals.append(v)
            return vals

        def fmt_sum(vals):
            return "=" + "".join(f"{v:.0f}" if i == 0 else (f"+{v:.0f}" if v >= 0 else f"{v:.0f}")
                                 for i, v in enumerate(vals))

        # 1) memori pola
        for tr in list(todo):
            hint = self.recipe_hints.get(tr.row)
            if not hint:
                continue
            parts = []
            for lbl in hint:
                m = [s for s in self._cands(tr) if s.idx not in used and clean_label(s.label) == clean_label(lbl)
                     and s not in parts]
                if not m:
                    parts = None
                    break
                parts.append(max(m, key=lambda x: self._pos_bonus(tr, x)))
            vals = value_of(tr, parts) if parts else None
            if vals is None:
                continue
            out[tr.row] = {"value": sum(vals), "vals": vals, "formula": fmt_sum(vals) if len(vals) > 1 else None,
                           "src": parts[0], "method": "Memori pola", "score": 90.0,
                           "why": "pola angka tidak tersedia; memakai resep bank ini dari periode sebelumnya: "
                                  + " + ".join(f"'{p.label}'" for p in parts)}
            used.update(p.idx for p in parts)
            todo.remove(tr)

        # 2) nama akun / kamus padanan
        pairs = []
        for tr in todo:
            for sr in self._cands(tr):
                if sr.idx in used or not sr.values or _is_total(sr.label) or _ocr_partial(sr):
                    continue
                base = self._support(tr, sr)
                if base < 80:
                    continue
                if sr.parent and self._is_parent_name(tr, sr.parent) and \
                        similarity(tr.label, f"{sr.parent} {sr.label}") < 90:
                    continue  # baris template = induknya (mis. OCI = Keuntungan + Kerugian) -> lapis 2b
                v = self._fb_value(tr, sr)
                plaus, _ = self._plausibility(tr, v)
                pairs.append((base + self._pos_bonus(tr, sr) + plaus, tr, sr))
        pairs.sort(key=lambda x: -x[0])
        done = set()
        for score, tr, sr in pairs:
            if tr.row in done or sr.idx in used:
                continue
            v = self._fb_value(tr, sr)
            if v is None:
                continue
            last = self.last_value(tr)
            if last and v and not (0.1 <= abs(v / last) <= 10):
                continue  # angka tidak wajar vs periode lalu -> jangan dipakai
            parts, vals = [sr], [v]
            conv = self.conventions.get(tr.section, {}).get(clean_label(tr.label), [])
            for extra in conv:
                m = [s for s in self._cands(tr) if s.idx not in used and all(s is not p for p in parts)
                     and clean_label(s.label).startswith(clean_label(extra))]
                if m:
                    ev = self._fb_value(tr, m[0])
                    if ev is not None:
                        parts.append(m[0])
                        vals.append(ev)
            done.add(tr.row)
            used.update(p.idx for p in parts)
            why = "pola angka tidak tersedia; dikenali dari nama akun '" + sr.label + "'"
            if len(parts) > 1:
                why += " + kebiasaan penjumlahan: " + " + ".join(f"'{p.label}'" for p in parts[1:])
            out[tr.row] = {"value": sum(vals), "vals": vals, "formula": fmt_sum(vals) if len(vals) > 1 else None,
                           "src": sr, "method": "Nama akun", "score": round(min(score, 100.0), 1), "why": why}

        # 2b) template 1 baris, laporan dipecah jadi sub-akun (mis. OCI = Keuntungan + Kerugian)
        for tr in todo:
            if tr.row in out:
                continue
            kids = [s for s in self._cands(tr) if s.idx not in used and s.parent and s.values
                    and not _ocr_partial(s) and self._is_parent_name(tr, s.parent)]
            if 2 <= len(kids) <= 4:
                vals = value_of(tr, kids)
                if vals is not None:
                    out[tr.row] = {"value": sum(vals), "vals": vals, "formula": fmt_sum(vals), "src": kids[0],
                                   "method": "Nama akun", "score": 80.0,
                                   "why": f"pola angka tidak tersedia; = jumlah sub-akun '{kids[0].parent}'"}
                    used.update(k.idx for k in kids)

        # 3) penyeimbang Neraca: akun baru yang menutup selisih total -> dimasukkan ke sisi yang benar
        self._balance_repair(recipes, out, used)
        self._income_repair(recipes, out, used)
        self._derive_from_totals(recipes, out)
        self._income_repair(recipes, out, used)  # selisih yang baru kelihatan setelah akun diturunkan
        self._named_gap_fill(recipes, out, used, "CAP")
        return out

    def _is_parent_name(self, tr, parent_label):
        names = lookup(self.aliases, tr.section, tr.label, tr.parent) or []
        return similarity(tr.label, parent_label) >= 80 or clean_label(parent_label) in names

    def _fb_value(self, tr, sr):
        """Nilai untuk jalur tanpa pola: ikuti konvensi tanda template (akun pengurang -/- ditulis negatif)."""
        v, _ = self.value_for(tr, sr)
        if v:
            hist = [h for _, h in self.history(tr, 4) if h]
            if v > 0 and ((hist and all(h < 0 for h in hist)) or "-/-" in sr.label):
                v = -v
        return v

    def _balance_repair(self, recipes, out, used):
        """Neraca harus seimbang dengan laporan. Akun laporan yang belum terpakai dikenali sisinya
        dari posisinya di laporan (sebelum TOTAL ASET = aset, sebelum TOTAL LIABILITAS = liabilitas,
        sesudahnya = ekuitas). Kombinasi akun yang jumlahnya persis menutup selisih total dimasukkan:
        ke baris template yang namanya cocok, atau ke Aset/Liabilitas/Ekuitas lainnya."""
        from itertools import combinations

        from .matcher import evaluate_column

        rows = {r.row: r for r in self.model.rows}
        bs_rows = [r for r in self.model.rows if r.section == "BS"]
        src = [x for x in self.source if x.section == "BS"]

        def terms_of(row):
            if row in out:
                return list(out[row].get("vals") or [out[row]["value"]])
            rec = recipes.get(row)
            if rec:
                vs = [self.cur_value(x, rows[row].section) for x, _ in rec.parts]
                if all(v is not None for v in vs):
                    return [sg * v for (_, sg), v in zip(rec.parts, vs)]
            return None

        def computed():
            vals = {}
            for r in bs_rows:
                t = terms_of(r.row)
                if t is not None:
                    vals[r.row] = sum(t)
            return evaluate_column(self.model, self.target_col, self.ref_col, vals)

        def tpl(pat):
            return next((r for r in bs_rows if re.match(pat, clean_label(r.label))), None)

        def rep(pat):
            x = next((x for x in src if re.match(pat, clean_label(x.label))), None)
            return x, (self.cur_value(x, "BS") if x else None)

        t_aset, t_le = tpl(r"^total aset$"), tpl(r"^(jumlah|total) (kewajiban|liabilitas) dan (modal|ekuitas)$")
        t_liab = tpl(r"^total (liabilitas|kewajiban)$")
        (s_aset, v_aset) = rep(r"^(total|jumlah) (aset|assets?|aktiva)$")
        (s_le, v_le) = rep(r"^(jumlah|total) (liabilitas|kewajiban|liabilities) (dan|and) (ekuitas|modal|equity|equities)$")
        s_liab, _ = rep(r"^(jumlah|total) (liabilitas|kewajiban|liabilities|liability)$")
        if not t_aset or not s_aset:
            return

        def side_pos(x):
            if x.idx < s_aset.idx:
                return "A"
            return "L" if s_liab and x.idx < s_liab.idx else "E"

        side_cache = {}

        def side_src(x):
            """Sisi akun: dari baris template yang namanya paling mirip (tabel aset & liabilitas bisa
            berdampingan di satu halaman), kalau tidak ada yang mirip -> dari posisinya di laporan."""
            if x.idx not in side_cache:
                best = max(((self._support(r, x), r) for r in bs_rows if r.row not in self._formula_rows),
                           key=lambda p: p[0], default=(0, None))
                side_cache[x.idx] = side_tpl(best[1]) if best[0] >= 85 else side_pos(x)
            return side_cache[x.idx]

        def side_tpl(r):
            if r.row < t_aset.row:
                return "A"
            return "L" if t_liab and r.row < t_liab.row else "E"

        used_labels = {clean_label(x.label) for x in src if x.idx in used}
        parents = {clean_label(x.parent) for x in src if x.parent}
        pool = []
        for x in src:
            if x.idx in used or not x.values or _is_total(x.label) or clean_label(x.label) in parents:
                continue
            if x.parent and clean_label(x.parent) in used_labels:
                continue
            v = self.cur_value(x, "BS")
            if v is None or abs(v) < 0.5:
                continue
            pool.append((x, v))

        others = {"A": tpl(r"^aset lainnya$"), "L": tpl(r"^liabilitas lainnya$"), "E": tpl(r"^ekuitas lainnya$")}
        filled = {r.row for r in bs_rows if terms_of(r.row) is not None}
        for sides, t_row, rep_v in ((("A",), t_aset, v_aset), (("L", "E"), t_le, v_le)):
            if t_row is None or rep_v is None:
                continue
            comp = computed().get(t_row.row)
            if comp is None:
                continue
            diff = rep_v - comp
            if abs(diff) <= 5:
                continue
            cand = sorted([(x, v) for x, v in pool if side_src(x) in sides], key=lambda p: -abs(p[1]))[:16]
            pick = None
            for k in range(len(cand), 0, -1):
                for combo in combinations(cand, k):
                    if abs(sum(v for _, v in combo) - diff) <= 3 + k:  # pembulatan juta rupiah di laporan
                        pick = combo
                        break
                if pick:
                    break
            if not pick:
                continue
            for x, v in pick:
                side = side_src(x)
                # 1) baris template kosong yang namanya cocok, di sisi yang sama
                named = [(self._support(r, x), r) for r in bs_rows
                         if r.row not in filled and r.row not in self._formula_rows and side_tpl(r) == side]
                named = [p for p in named if p[0] >= 85 and (self._alias_score(p[1], x) or
                                                              fuzz.token_sort_ratio(clean_label(p[1].label),
                                                                                    clean_label(x.label)) >= 80)]
                if named:
                    r = max(named, key=lambda p: p[0])[1]
                    before = computed().get(t_row.row)
                    out[r.row] = {"value": v, "vals": [v], "formula": None, "src": x, "method": "Penyeimbang",
                                  "score": 75.0, "why": f"akun baru '{x.label}' (sisi {'Aset' if side == 'A' else 'Liabilitas' if side == 'L' else 'Ekuitas'} di laporan) "
                                                        "diisi supaya Neraca = laporan"}
                    after = computed().get(t_row.row)
                    if before is not None and after is not None and abs(after - before - v) <= 1:
                        filled.add(r.row)
                        used.add(x.idx)
                        continue
                    del out[r.row]  # baris itu tidak ikut dijumlah di total template -> pakai '... lainnya'

                # 2) masuk ke '... lainnya' di sisi yang sama
                r = others.get(side) or others.get("L" if side == "E" else side)
                if r is None:
                    continue
                base = terms_of(r.row) or []
                fb = out.get(r.row) or {"src": x, "method": "Penyeimbang", "score": 70.0,
                                         "why": "sesuai pola" if r.row in recipes else "pola angka tidak tersedia"}
                new_vals = base + [v]
                fb.update({"value": sum(new_vals), "vals": new_vals,
                           "formula": "=" + "".join(f"{t:.0f}" if i == 0 else (f"+{t:.0f}" if t >= 0 else f"{t:.0f}")
                                                    for i, t in enumerate(new_vals))})
                if fb["method"] not in ("Nama akun", "Memori pola"):
                    fb["method"] = "Penyeimbang"
                fb["why"] += f"; ditambah akun baru '{x.label}' supaya Neraca = laporan"
                out[r.row] = fb
                filled.add(r.row)
                used.add(x.idx)

    def _row_terms(self, row, recipes, out):
        if row in out:
            return list(out[row].get("vals") or [out[row]["value"]])
        rec = recipes.get(row)
        if rec:
            tr = next(r for r in self.model.rows if r.row == row)
            vs = [self.cur_value(x, tr.section) for x, _ in rec.parts]
            if all(v is not None for v in vs):
                return [sg * v for (_, sg), v in zip(rec.parts, vs)]
        return None

    def _income_repair(self, recipes, out, used):
        """Laba Rugi: akun laporan yang belum terpakai (mis. 'Pendapatan Asuransi - Neto' yang baru
        muncul) dan persis menutup selisih total template vs laporan dimasukkan ke pos 'lainnya'
        di blok yang sama (operasional / non operasional / penghasilan komprehensif lain)."""
        from itertools import combinations

        from .matcher import reconcile

        is_rows = [r for r in self.model.rows if r.section == "IS"]
        src = [x for x in self.source if x.section == "IS"]
        if not is_rows or not src:
            return

        def tpl(pat, after=0):
            return next((r for r in is_rows if r.row > after and re.match(pat, clean_label(r.label))), None)

        after_tax = tpl(r"^laba rugi (periode|tahun) berjalan setelah pajak")
        oci_other = tpl(r"^lainnya$", after_tax.row) if after_tax else None
        blocks = [(r"^laba operasional$", tpl(r"^pendapatan lainnya$"), tpl(r"^beban lainnya$")),
                  (r"^laba rugi non operasional$", tpl(r"^pendapatan beban non operasional lainnya$"),
                   tpl(r"^pendapatan beban non operasional lainnya$")),
                  (r"^total laba komprehensif tahun berjalan$", oci_other, oci_other)]
        expense_row = {r.row for r in is_rows if re.match(r"\s*beban", r.label, re.I)}
        parents = {clean_label(x.parent) for x in src if x.parent}
        start = min(x.idx for x in src) - 1
        lo_row = 0  # baris template awal blok yang sedang dicek

        def values_now():
            vals = {}
            for r in self.model.rows:
                t = self._row_terms(r.row, recipes, out)
                if t is not None:
                    vals[r.row] = sum(t)
            return vals

        for total_pat, plus_row, minus_row in blocks:
            checks = reconcile(self, values_now())
            chk = next((c for c in checks
                        if c["Seksi"] == "IS" and re.match(total_pat, clean_label(c["Total (template)"]))), None)
            if chk is None:
                continue
            if total_pat.startswith("^total laba komprehensif"):
                # penghasilan komprehensif lain: hanya akun SETELAH laba bersih (bukan pajak dsb.)
                net = next((c for c in checks if c["Seksi"] == "IS" and c["Status"] != "BEDA"
                            and re.match(r"^laba rugi (periode|tahun) berjalan setelah pajak", clean_label(c["Total (template)"]))),
                           None)
                if net is None:
                    continue
                start = max(start, net["_src_idx"])
                lo_row = max(lo_row, net["Baris"])
            end = chk["_src_idx"]
            diff = chk["Di laporan"] - chk["Hasil hitung"]
            if chk["Status"] != "BEDA" or abs(diff) <= 5:
                start = end
                lo_row = chk["Baris"]
                continue
            pool = []
            for x in src:
                if not (start < x.idx < end) or x.idx in used or not x.values \
                        or (_is_total(x.label) and not _is_subtotalish(x.label)) or _is_grand_total(x.label) \
                        or clean_label(x.label) in parents:
                    continue
                v = self.cur_value(x, "IS")
                if v is not None and abs(v) >= 0.5:
                    pool.append((x, v))
            pool = sorted(pool, key=lambda p: -abs(p[1]))[:14]
            pick = None
            for k in range(1, min(4, len(pool)) + 1):
                hits = []
                for combo in combinations(pool, k):
                    tot = sum(v for _, v in combo)
                    for sg in (1, -1):  # beban kadang ditulis positif di laporan
                        if abs(sg * tot - diff) <= 3 + k:
                            hits.append((sum(_is_subtotalish(x.label) for x, _ in combo), sg != 1, combo, sg))
                if hits:
                    hits.sort(key=lambda h: (h[0], h[1]))  # utamakan akun rinci (bukan subtotal) & tanda asli
                    pick = (hits[0][2], hits[0][3])
                    break
            start = end
            if not pick:
                lo_row = chk["Baris"]
                continue
            combo, sg = pick
            # akun yang punya baris template kosong bernama mirip di blok yang sama -> isi baris itu
            blank = [r for r in is_rows if lo_row < r.row < chk["Baris"] and r.row not in self._formula_rows
                     and self._row_terms(r.row, recipes, out) is None]
            placed_all = True
            for x, v in combo:
                cand = max(((max(self._support(r, x), similarity(r.label, x.label)), r) for r in blank),
                           key=lambda p: p[0], default=(0, None))
                if cand[0] < 70:
                    placed_all = False
                    break
            if placed_all and len(combo) >= 1:
                saved_rows = {}
                for x, v in combo:
                    r = max(blank, key=lambda rr: max(self._support(rr, x), similarity(rr.label, x.label)))
                    val = (-1 if r.row in expense_row else 1) * sg * v
                    saved_rows[r.row] = out.get(r.row)
                    out[r.row] = {"value": val, "vals": [val], "formula": None, "src": x, "method": "Penyeimbang",
                                  "score": 70.0, "why": f"akun '{x.label}' tidak ada di pola acuan; dimasukkan ke baris "
                                                        "bernama mirip supaya total Laba Rugi = laporan"}
                    blank = [b for b in blank if b.row != r.row]
                after = next((c["Hasil hitung"] for c in reconcile(self, values_now()) if c["Baris"] == chk["Baris"]),
                             None)
                if after is not None and abs(after - chk["Hasil hitung"] - diff) <= 3 + len(combo):
                    used.update(x.idx for x, _ in combo)
                    lo_row = chk["Baris"]
                    continue
                for rr, old in saved_rows.items():
                    if old is None:
                        out.pop(rr, None)
                    else:
                        out[rr] = old
            target = plus_row if diff > 0 else minus_row
            if target is None or target.row in self._formula_rows:
                continue
            flip = -1 if target.row in expense_row else 1
            parts = [flip * sg * v for _, v in combo]
            base = self._row_terms(target.row, recipes, out) or []
            before = chk["Hasil hitung"]
            saved = out.get(target.row)
            fb = dict(saved) if saved else {"src": combo[0][0], "method": "Penyeimbang", "score": 70.0,
                                            "why": "sesuai pola" if target.row in recipes else "pola angka tidak tersedia"}
            new_vals = base + parts
            fb.update({"value": sum(new_vals), "vals": new_vals,
                       "formula": "=" + "".join(f"{t:.0f}" if i == 0 else (f"+{t:.0f}" if t >= 0 else f"{t:.0f}")
                                                for i, t in enumerate(new_vals))})
            if fb["method"] not in ("Nama akun", "Memori pola"):
                fb["method"] = "Penyeimbang"
            fb["why"] = fb["why"] + "; ditambah akun baru " + " + ".join(f"'{x.label}'" for x, _ in combo) \
                + " supaya total Laba Rugi = laporan"
            out[target.row] = fb
            after = next((c["Hasil hitung"] for c in reconcile(self, values_now()) if c["Baris"] == chk["Baris"]), None)
            if after is None or abs(after - before - diff) > 3 + len(combo):
                if saved:
                    out[target.row] = saved
                else:
                    del out[target.row]
                continue
            used.update(x.idx for x, _ in combo)
            lo_row = chk["Baris"]

    def _named_gap_fill(self, recipes, out, used, section):
        """Total masih beda persis sebesar satu akun laporan yang belum dipakai, dan ada baris template
        kosong (di dalam rumus total itu) yang namanya cocok -> isi baris itu (mis. AT 1 baru di KPMM)."""
        from .matcher import evaluate_column, reconcile

        def values_now():
            vals = {}
            for r in self.model.rows:
                t = self._row_terms(r.row, recipes, out)
                if t is not None:
                    vals[r.row] = sum(t)
            return vals

        for _ in range(4):
            vals = values_now()
            bad = [c for c in reconcile(self, vals) if c["Seksi"] == section and c["Status"] == "BEDA"]
            done = False
            for c in sorted(bad, key=lambda c: c["Baris"]):
                diff = c["Di laporan"] - c["Hasil hitung"]
                srcs = [x for x in self.source if x.section == section and x.idx not in used and x.values
                        and (v := self.cur_value(x, section)) is not None and abs(abs(v) - abs(diff)) <= 3]
                base = evaluate_column(self.model, self.target_col, self.ref_col, vals).get(c["Baris"])
                pairs = []
                for tr in self._value_rows:
                    if tr.section != section or tr.row in vals or tr.row in self._formula_rows:
                        continue
                    t = evaluate_column(self.model, self.target_col, self.ref_col, {**vals, tr.row: 1.0}).get(c["Baris"])
                    if base is None or t is None or abs(abs(t - base) - 1) > 1e-6:
                        continue
                    for x in srcs:
                        if self._support(tr, x) >= 85:
                            pairs.append((tr, x, t - base))
                if len(pairs) != 1:
                    continue
                tr, x, k = pairs[0]
                v = diff / k
                out[tr.row] = {"value": v, "vals": [v], "formula": None, "src": x, "method": "Penyeimbang",
                               "score": 75.0, "why": f"akun '{x.label}' tidak ada di pola acuan; diisi karena "
                                                     f"{c['Total (template)']} kurang persis sebesar akun ini"}
                used.add(x.idx)
                done = True
                break
            if not done:
                break

    def _derive_from_totals(self, recipes, out):
        """Akun yang wajib diisi tapi angkanya tidak terbaca (mis. OCR) dihitung dari total laporan:
        kalau tepat SATU akun kosong di dalam rumus total yang berbeda, nilainya = selisihnya
        (mis. Beban bunga = Pendapatan bunga - Pendapatan bunga bersih)."""
        from .matcher import evaluate_column, reconcile

        def values_now():
            vals = {}
            for r in self.model.rows:
                t = self._row_terms(r.row, recipes, out)
                if t is not None:
                    vals[r.row] = sum(t)
            return vals

        def should(tr):
            col = self.ref_cols.get(tr.section)
            if self._ref_usable(tr.section):
                return col is not None and tr.numeric(col) is not None
            return self.usually_filled(tr)

        for _ in range(8):
            vals = values_now()
            bad = sorted((c for c in reconcile(self, vals) if c["Status"] == "BEDA" and c["Seksi"] in ("IS", "BS")
                          and not c["Total (template)"].startswith("Aset =")), key=lambda c: c["Baris"])
            changed = False
            for c in bad:
                blanks = [tr for tr in self._value_rows if tr.section == c["Seksi"] and tr.row not in vals
                          and tr.row not in self._formula_rows and should(tr)]
                coef = {}
                base = evaluate_column(self.model, self.target_col, self.ref_col, vals).get(c["Baris"])
                for tr in blanks:
                    t = evaluate_column(self.model, self.target_col, self.ref_col, {**vals, tr.row: 1.0}).get(c["Baris"])
                    if base is not None and t is not None and abs(abs(t - base) - 1) < 1e-6:
                        coef[tr.row] = t - base
                if len(coef) != 1:
                    continue
                row, k = next(iter(coef.items()))
                tr = next(r for r in self.model.rows if r.row == row)
                v = (c["Di laporan"] - c["Hasil hitung"]) / k
                last = self.last_value(tr)
                if last and (v / last <= 0 or not 0.1 <= abs(v / last) <= 10):
                    continue  # hasil tidak wajar -> biarkan kosong
                out[row] = {"value": v, "vals": [v], "formula": None, "src": next(
                    (x for x in self.source if x.idx == c.get("_src_idx")), self.source[0]),
                    "method": "Turunan total", "score": 60.0,
                    "why": f"angka akun tidak terbaca di laporan; dihitung dari total '{c['Akun laporan']}' "
                           f"supaya {c['Total (template)']} = laporan"}
                changed = True
                break
            if not changed:
                break

    def _pos_bonus(self, tr, sr):
        return 6 * max(0.0, 1 - abs(self._tpl_pos(tr) - self._src_pos.get(sr.idx, 0.5)) / 0.25)

    # ------------------------------------------------------------ main
    def run(self, cur_idx_override=None):
        return self.run_main() + self.run_extra()

    def run_main(self):
        self._detect_scale()
        results, used = {}, set()
        recipes = {}
        todo = [tr for tr in self._value_rows if tr.row not in self._formula_rows]
        # akun dengan angka acuan besar & unik dulu, supaya tidak 'dicuri' baris lain
        todo.sort(key=lambda tr: -abs(tr.numeric(self.ref_cols.get(tr.section)) or 0)
                  if self.ref_cols.get(tr.section) else 0)
        reasons = {}
        for tr in todo:
            rec, why = self.find_recipe(tr, used)
            if rec:
                recipes[tr.row] = rec
                used.update(s.idx for s, _ in rec.parts)
            else:
                reasons[tr.row] = why
        self.recipes = recipes
        fallback = self._fallback(recipes, reasons, used) if self.fallback else {}

        out = []
        for tr in self.model.rows:
            prev = self.last_value(tr)
            if tr.row in self._formula_rows:
                out.append(MatchResult(tr.row, tr.section, tr.label, tr.parent, "Formula", prev))
                continue
            col = self.ref_cols.get(tr.section)
            ref_h = tr.numeric(col) if col else None
            ref_ok = self._ref_usable(tr.section)
            should = (ref_h is not None) if ref_ok else self.usually_filled(tr)
            res = MatchResult(tr.row, tr.section, tr.label, tr.parent,
                              "Nilai" if should else "Biasanya kosong", prev)
            rec = recipes.get(tr.row)
            if tr.row in fallback:
                fb = fallback[tr.row]
                res.value, res.formula = fb["value"], fb.get("formula")
                res.source_idx, res.source_label = fb["src"].idx, fb["src"].label
                res.method, res.score = fb["method"], fb.get("score", 0.0)
                res.note = "🟡 " + fb["why"] + " — CEK"
            elif rec:
                vals = [self.cur_value(s, tr.section) for s, _ in rec.parts]
                s0 = rec.parts[0][0]
                res.source_idx, res.source_label = s0.idx, s0.label
                res.method = "Pola angka" if rec.kind == "single" else "Pola penjumlahan"
                res.score = 100.0
                notes = list(rec.notes)
                if rec.kind == "sum":
                    notes.insert(0, "= " + " + ".join(f"'{s.label}'" for s, _ in rec.parts)
                                 + f" (sesuai pola {self.model.period_cols.get(col)})")
                if any(v is None for v in vals):
                    notes.append("angka periode berjalan tidak ada di laporan — cek manual")
                else:
                    res.value = sum(sg * v for (_, sg), v in zip(rec.parts, vals))
                    if rec.kind == "sum":
                        # gaya analis: '=1720252673+39443243' -> rinciannya tetap terlihat di Excel
                        terms = [sg * v for (_, sg), v in zip(rec.parts, vals)]
                        res.formula = "=" + "".join(
                            (f"{t:.0f}" if i == 0 else (f"+{t:.0f}" if t >= 0 else f"{t:.0f}"))
                            for i, t in enumerate(terms))
                    if any(sg == -1 for _, sg in rec.parts):
                        notes.append("tanda dibalik sesuai pola acuan")
                res.note = "; ".join(notes)
            elif ref_h is None and col is not None:
                # kosong di periode acuan: tidak diisi, tapi beri tahu kalau laporan punya
                # akun dengan nama sama & angkanya tidak nol (kemungkinan akun baru)
                hint = self.best_label_match(tr, min_score=90)
                v = self.cur_value(hint[1], tr.section) if hint else None
                if v:
                    res.note = (f"⚠ kosong di periode acuan ({self.model.period_cols.get(col)}), tapi laporan punya "
                                f"'{hint[1].label}' = {v:,.0f} — akun baru? tidak diisi")
            elif ref_h is not None:
                res.note = "⚠ " + (reasons.get(tr.row) or "pola tidak ketemu") + " — tidak diisi"
                hint = self.best_label_match(tr, min_score=80)
                if hint:
                    res.source_idx, res.source_label = hint[1].idx, hint[1].label
                    res.method = "Saran nama akun"
                    res.score = round(min(hint[0], 100.0), 1)
            out.append(res)
        return out

    # ------------------------------------------------------------ rasio & NPL
    def run_extra(self):
        """Baris rasio (LDR, BOPO, ROA, ROE, NIM, NPL %, GWM, PDN) & NPL kolektibilitas.
        Periode acuan = periode yang sama tahun lalu. Entitas/kolom mengikuti pola."""
        from .template_model import is_ref_formula

        ref_per = (self.month, self.year - 1)
        ref_col = self.model.find_period_col(*ref_per)
        ref_label = self.model.period_cols.get(ref_col, f"{ref_per[0]:02d}/{ref_per[1]}")
        out = []
        used = set()
        ratio_pool = [s for s in self.source_all if s.values and not getattr(s, "cats", None)
                      and all(abs(v) < 1000 for v in s.values) and s.section in ("OTHER", "CAP", "?")]
        aq_rows = [s for s in self.source_all if getattr(s, "cats", None) and s.cols]
        for tr in getattr(self.model, "extra_rows", None) or []:
            prev = self.last_value(tr)
            ref_cell = tr.cells.get(ref_col) if ref_col else None
            if is_ref_formula(tr.cells.get(self.target_col)):
                out.append(MatchResult(tr.row, tr.section, tr.label, None, "Formula", prev))
                continue
            if is_ref_formula(ref_cell):
                # pola acuan berupa rumus -> rumus yang sama digeser ke kolom tujuan
                from .matcher import translate_formula

                res = MatchResult(tr.row, tr.section, tr.label, None, "Nilai", prev)
                res.formula = translate_formula(ref_cell, ref_col, self.target_col, tr.row)
                res.method, res.score = "Rumus acuan", 100.0
                res.source_label = f"rumus {ref_label}"
                res.note = f"rumus periode acuan {ref_label} digeser: {res.formula}"
                out.append(res)
                continue
            res = MatchResult(tr.row, tr.section, tr.label, None, "Nilai" if ref_cell is not None else "Biasanya kosong",
                              prev)
            if ref_cell is None:
                if ref_col is None:
                    res.note = f"⚠ periode acuan {ref_label} belum ada di template — tidak diisi"
                out.append(res)
                continue
            if tr.section == "NPL" and isinstance(ref_cell, str):
                self._npl_formula(tr, ref_cell, ref_per, aq_rows, res)
            else:
                h = tr.numeric(ref_col)
                self._ratio(tr, h, ref_per, ratio_pool, used, res, ref_label)
            out.append(res)
        return out

    def _ratio(self, tr, h, ref_per, pool, used, res, ref_label):
        if h is None:
            res.note = "⚠ nilai periode acuan bukan angka — tidak diisi"
            return
        hits = []
        for s in pool:
            if s.idx in used:
                continue
            meta = s.cols if (s.cols and len(s.cols) == len(s.values)) else None
            for k, v in enumerate(s.values):
                if abs(v - h) > 0.0051:
                    continue
                if meta and any(p for p, _ in meta):
                    if meta[k][0] != ref_per:
                        continue
                    ent = meta[k][1]
                    cur = [i for i, (p, e) in enumerate(meta) if p == self.period and e == ent] or \
                        [i for i, (p, e) in enumerate(meta) if p == self.period]  # label entitas header basi
                    ci = cur[0] if len(cur) >= 1 else None
                else:
                    ci = k - 1 if k % 2 == 1 else None  # pasangan [kini, lalu]
                if ci is not None and ci < len(s.values):
                    hits.append((s, ci))
        if len(hits) > 1:
            kw = _ratio_keywords(tr.label)
            ranked = sorted(hits, key=lambda x: -_kw_score(kw, x[0]))
            if _kw_score(kw, ranked[0][0]) > _kw_score(kw, ranked[1][0]):
                hits = ranked[:1]
            elif len({round(x[0].values[x[1]], 4) for x in hits}) == 1:
                hits = ranked[:1]  # semua kandidat memberi angka yang sama
        if not hits:
            fb = self._ratio_by_name(tr, h, ref_per, pool, used)
            if fb:
                s, ci, rv = fb
                used.add(s.idx)
                res.value = s.values[ci]
                res.source_idx, res.source_label = s.idx, s.label
                res.method, res.score = "Nama akun", 80.0
                res.note = (f"🟡 angka acuan {h:g} ({ref_label}) tidak ada persis (laporan: {rv:g}, kemungkinan "
                            "di-restate); dikenali dari nama rasio — CEK")
                return
        if len(hits) != 1:
            res.note = ("⚠ " + ("beberapa rasio cocok dengan angka acuan" if hits else
                                f"angka acuan {h:g} ({ref_label}) tidak ditemukan di tabel rasio") + " — tidak diisi")
            return
        s, ci = hits[0]
        used.add(s.idx)
        v = s.values[ci]
        res.source_idx, res.source_label = s.idx, s.label
        res.method, res.score = "Pola angka", 100.0
        if h and abs(v) > 20 * abs(h) and 0.2 <= abs(v / 100 / h) <= 5:
            # '4,46' terbaca '446' (koma desimal hilang, biasanya OCR) -> skala rasio periode acuan
            v = v / 100
            res.note = "🟡 koma desimal hilang di laporan (mis. OCR) → dibagi 100 — CEK"
        res.value = v

    def _ratio_by_name(self, tr, h, ref_per, pool, used):
        """Rasio tanpa pola angka: cari dari nama rasio, hanya kalau angka pembandingnya di laporan
        beda tipis (±10%) dari template — kalau beda jauh, analis memakai definisi lain."""
        kw = _ratio_keywords(tr.label)
        if not kw or not h:
            return None
        cands = []
        for s in pool:
            if s.idx in used or _kw_score(kw, s) <= 0:
                continue
            meta = s.cols if (s.cols and len(s.cols) == len(s.values)) else None
            if meta and any(p for p, _ in meta):
                ri = [i for i, (p, _) in enumerate(meta) if p == ref_per]
                ci = [i for i, (p, _) in enumerate(meta) if p == self.period]
                if not ri or not ci:
                    continue
                ri, ci = ri[0], ci[0]
            elif len(s.values) == 2:
                ci, ri = 0, 1
            else:
                continue
            rv = s.values[ri]
            if rv and 0.9 <= rv / h <= 1.1:
                cands.append((_kw_score(kw, s), s, ci, rv))
        if not cands:
            return None
        cands.sort(key=lambda c: -c[0])
        if len(cands) > 1 and cands[0][0] == cands[1][0] and cands[0][1].values[cands[0][2]] != \
                cands[1][1].values[cands[1][2]]:
            return None
        _, s, ci, rv = cands[0]
        return s, ci, rv

    def _npl_formula(self, tr, formula, ref_per, aq_rows, res):
        from .text import parse_number

        m = re.match(r"^=\s*\(([^()]*)\)\s*/\s*([\d.]+)\s*$", formula.strip()) or \
            re.match(r"^=\s*([\d.]+)\s*/\s*([\d.]+)\s*$", formula.strip())  # satu komponen: '=30643981/1000'

        if not m:
            res.note = "⚠ rumus periode acuan tidak dikenali — tidak diisi"
            return
        comps_txt = [c.strip() for c in m.group(1).split("+")]
        divisor = m.group(2)
        comps = [parse_number(c) for c in comps_txt]
        if any(c is None for c in comps):
            res.note = "⚠ rumus periode acuan tidak dikenali — tidak diisi"
            return
        want = {"current": {"L"}, "special": {"DPK"}, "npl": {"KL", "D", "M"}}
        key = "current" if tr.label.lower().startswith("current") else (
            "special" if tr.label.lower().startswith("special") else "npl")
        cats = want[key]
        # kandidat sel (baris, kolom) untuk tiap komponen di periode acuan
        options = []
        for c in comps:
            if abs(c) < 10:  # 0 / angka sangat kecil: tidak bisa dilacak unik -> dipertahankan
                options.append(None)
                continue
            cands = []
            for s in aq_rows:
                for i, (p, _) in enumerate(s.cols):
                    if p == ref_per and i < len(s.values) and s.cats[i] in cats and abs(s.values[i] - c) <= 0.5:
                        cands.append((s, i))
            kredit = [x for x in cands if _in_kredit(x[0])]
            options.append(kredit or cands)

        def cur_of(s, i):
            cat = s.cats[i]
            cur = [j for j, (p, _) in enumerate(s.cols) if p == self.period and s.cats[j] == cat]
            return s.values[cur[0]] if cur and cur[0] < len(s.values) else None

        chosen = [None] * len(comps)
        taken = set()
        for k, opts in enumerate(options):
            if opts and len(opts) == 1:
                chosen[k] = opts[0]
                taken.add((opts[0][0].idx, opts[0][1]))
        # komponen ambigu (mis. angka sama di baris induk & anaknya): pilih kedalaman
        # baris yang sama dengan komponen yang sudah pasti
        depths = [len(getattr(ch[0], "ancestors", None) or []) for ch in chosen if ch]
        pref = max(set(depths), key=depths.count) if depths else None
        for k, opts in enumerate(options):
            if opts is None or chosen[k]:
                continue
            free = [o for o in opts if (o[0].idx, o[1]) not in taken]
            if pref is not None and len(free) > 1:
                same = [o for o in free if len(getattr(o[0], "ancestors", None) or []) == pref]
                free = same or free
            if len(free) > 1 and len({cur_of(*o) for o in free}) == 1:
                free = free[:1]  # semua kandidat memberi angka periode berjalan yang sama
            if len(free) != 1:
                res.note = (f"⚠ komponen {comps[k]:,.0f} " + ("muncul di beberapa sel" if free else
                                                             "tidak ditemukan di tabel kualitas aset") + " — tidak diisi")
                return
            chosen[k] = free[0]
            taken.add((free[0][0].idx, free[0][1]))
        new_parts, notes = [], []
        for k, ch in enumerate(chosen):
            if ch is None:
                lit = comps_txt[k]
                new_parts.append((lit, comps[k]))
                notes.append(f"komponen {lit} dipertahankan (terlalu kecil untuk dilacak)")
                continue
            v = cur_of(*ch)
            if v is None:
                res.note = "⚠ angka periode berjalan tidak ada di tabel kualitas aset — tidak diisi"
                return
            new_parts.append((f"{v:.0f}", v))
        res.formula = "=(" + "+".join(t for t, _ in new_parts) + ")/" + divisor
        res.value = sum(v for _, v in new_parts) / float(divisor)
        res.method, res.score = "Pola angka", 100.0
        res.source_label = f"Kualitas Aset: {len(new_parts)} komponen ({'/'.join(sorted(cats))})"
        res.note = "; ".join(dict.fromkeys(["rumus: " + res.formula] + notes))

    def recipe_memory(self):
        """row -> [label akun] untuk resep penjumlahan (disimpan & dipakai periode berikutnya)."""
        return {row: [sr.label for sr, _ in rec.parts] for row, rec in getattr(self, "recipes", {}).items()}

    def learned_conventions(self):
        """Resep penjumlahan yang ditemukan -> kebiasaan umum (per label template), supaya
        bisa dipakai bank lain / periode tanpa pola angka."""
        rows = {r.row: r for r in self.model.rows}
        out = {}
        for row, rec in getattr(self, "recipes", {}).items():
            if rec.kind != "sum" or row not in rows:
                continue
            tr = rows[row]
            main = max(rec.parts, key=lambda p: self._support(tr, p[0]))[0]
            if self._support(tr, main) < 80:
                continue  # akun utama tidak senama -> jangan dijadikan kebiasaan umum
            extras = [clean_label(sr.label) for sr, sg in rec.parts if sr is not main and sg > 0
                      and not _is_total(sr.label) and len(clean_label(sr.label)) > 3]
            if not extras:
                continue
            out.setdefault(tr.section, {})[clean_label(tr.label)] = extras
        return out

    # reconcile() memakai label_candidates & current_value — sudah kompatibel


_RATIO_KW = {
    "ldr": r"loan to deposit|\bldr\b|intermediasi|\brim\b", "bopo": r"bopo|beban operasional terhadap",
    "roa": r"\broa\b|return on asset", "roe": r"\broe\b|return on equity", "nim": r"\bnim\b|net interest margin",
    "npl gross": r"npl gross|gross npl|bruto", "npl net": r"npl net|net npl|neto", "gwm - idr": r"rupiah|gwm utama",
    "gwm - valas": r"valuta asing|valas", "posisi devisa": r"devisa|\bpdn\b",
}


def _ratio_keywords(label: str):
    low = label.lower()
    for k, pat in _RATIO_KW.items():
        if low.startswith(k):
            return pat
    return None


def _kw_score(pat, sr) -> int:
    if not pat:
        return 0
    txt = " ".join([sr.label] + list(getattr(sr, "ancestors", None) or []) + [sr.parent or ""])
    return 1 if re.search(pat, txt, re.I) else 0


def _in_kredit(sr) -> bool:
    txt = " ".join([sr.label] + list(getattr(sr, "ancestors", None) or []) + [sr.parent or ""])
    return bool(re.search(r"kredit|loan|pembiayaan", txt, re.I))


def _is_subtotalish(label: str) -> bool:
    return bool(re.search(r"(,.*\bdan\b.*(neto|bersih))|^pendapatan \(beban\)", label or "", re.I))


def _own_company_rows(model, rows):
    """Buang baris dari tabel milik bank lain yang ikut tercetak (mis. laporan grup Bank Mandiri
    di halaman koran BSI): judul tabelnya menyebut bank lain, bukan bank sheet ini."""
    from .banks import BANK_KEYWORDS, _keywords_for

    own = [k.upper() for k in _keywords_for(model)]
    others = [k for name, ks in BANK_KEYWORDS.items() if name != model.name for k in ks
              if not any(k in o or o in k for o in own)]

    def foreign(r):
        comp = (getattr(r, "company", None) or "").upper()
        return bool(comp) and not any(k in comp for k in own) and any(k in comp for k in others)

    return [r for r in rows if not foreign(r)]


def _ocr_partial(sr) -> bool:
    """Baris OCR yang sebagian angkanya hilang: tanpa konfirmasi pola angka, posisi kolomnya
    (Individual / Konsolidasian) tidak bisa dipastikan -> jangan dipakai untuk tebakan nama akun."""
    return bool(getattr(sr, "ocr", False) and sr.cols and len(sr.values) < len(sr.cols))


def _is_grand_total(label: str) -> bool:
    return bool(re.match(r"\s*(total|jumlah|laba \(rugi\)|laba bersih)", label or "", re.I))


def _is_total(label: str) -> bool:
    return bool(re.match(r"\s*(total|jumlah|laba \(rugi\)|laba bersih|pendapatan \(beban\).*(bersih|neto))",
                         label or "", re.I))


def _section_entity(model, section) -> str:
    """Judul seksi template: 'NERACA - Consol' -> KONS ; '... - Bank' / 'Bank only' -> IND."""
    title = (model.section_titles or {}).get(section, "") if hasattr(model, "section_titles") else ""
    t = title.lower()
    if "consol" in t or "konsol" in t:
        return "KONS"
    if re.search(r"\bbank\b|\bbo\b|bank only|individual", t):
        return "IND"
    return "KONS"


def clean(s):  # pragma: no cover - util kecil untuk debug
    return clean_label(s)
