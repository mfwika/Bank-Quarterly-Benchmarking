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


class StrictMatcher(Matcher):
    """Pencocokan ketat berbasis pola angka periode acuan."""

    def __init__(self, model, source_rows, target_col, aliases, period, entity_by_section=None, recipe_hints=None):
        super().__init__(model, source_rows, target_col, aliases, period=period)
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
            base = 0 if entity == "IND" else 2
            return base + (0 if role == "cur" else 1)
        if n == 2:
            return 0 if role == "cur" else 1
        return None

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
                cands.append((s, r))

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
        pool = [(s, r) for s, r in cands if r != 0 and not _is_total(s.label) and abs(r) <= 3 * abs(h) + 1]
        pool = pool[:120]
        by_val = defaultdict(list)
        for i, (s, r) in enumerate(pool):
            by_val[round(r)].append(i)
        def score(combos):
            out = []
            for c in combos:
                sups = [self._support(tr, pool[i][0]) for i in c]
                if max(sups) >= 60:
                    # utamakan kombinasi yang anggotanya bukan subtotal & lebih sedikit
                    pen = sum(8 for i in c if _is_subtotalish(pool[i][0].label))
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
            return None, "pola tidak ketemu di laporan (akun baru / angka pembanding di-restate?)"
        scored.sort(key=lambda x: x[0], reverse=True)
        if len(scored) > 1 and scored[0][0] - scored[1][0] < 5:
            return None, "beberapa kombinasi akun cocok dengan angka acuan — isi manual"
        parts = [(pool[i][0], 1) for i in scored[0][1]]
        parts.sort(key=lambda p: -self._support(tr, p[0]))
        return Recipe(parts, "sum", h), None

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

        out = []
        for tr in self.model.rows:
            prev = self.last_value(tr)
            if tr.row in self._formula_rows:
                out.append(MatchResult(tr.row, tr.section, tr.label, tr.parent, "Formula", prev))
                continue
            col = self.ref_cols.get(tr.section)
            ref_h = tr.numeric(col) if col else None
            res = MatchResult(tr.row, tr.section, tr.label, tr.parent,
                              "Nilai" if ref_h is not None else "Biasanya kosong", prev)
            rec = recipes.get(tr.row)
            if rec:
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
                    cur = [i for i, (p, e) in enumerate(meta) if p == self.period and e == ent]
                    ci = cur[0] if cur else None
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
        if len(hits) != 1:
            res.note = ("⚠ " + ("beberapa rasio cocok dengan angka acuan" if hits else
                                f"angka acuan {h:g} ({ref_label}) tidak ditemukan di tabel rasio") + " — tidak diisi")
            return
        s, ci = hits[0]
        used.add(s.idx)
        res.value = s.values[ci]
        res.source_idx, res.source_label = s.idx, s.label
        res.method, res.score = "Pola angka", 100.0

    def _npl_formula(self, tr, formula, ref_per, aq_rows, res):
        from .text import parse_number

        m = re.match(r"^=\s*\(([^()]*)\)\s*/\s*([\d.]+)\s*$", formula.strip())
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
        return {row: [sr.label for sr, _ in rec.parts] for row, rec in getattr(self, "recipes", {}).items()
                if rec.kind == "sum"}

    # reconcile() memakai label_candidates & current_value — sudah kompatibel


_RATIO_KW = {
    "ldr": r"loan to deposit|\bldr\b|intermediasi|\brim\b", "bopo": r"bopo|beban operasional terhadap",
    "roa": r"\broa\b|return on asset", "roe": r"\broe\b|return on equity", "nim": r"\bnim\b|net interest margin",
    "npl gross": r"npl gross|bruto", "npl net": r"npl net|neto", "gwm - idr": r"rupiah|gwm utama",
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
