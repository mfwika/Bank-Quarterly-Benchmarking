"""Bikin laporan publikasi SINTETIS (format OJK terbaru) dari angka yang sudah
ada di template — dipakai untuk uji end-to-end: sistem harus bisa
merekonstruksi kolom periode tsb dari PDF/Excel ini.

Susunan kolom angka meniru laporan publikasi:
  BANK (periode ini) | BANK (pembanding) | KONSOLIDASIAN (periode ini) | KONSOLIDASIAN (pembanding)
Pembanding neraca = Desember tahun lalu, laba rugi & KPMM = kuartal yg sama tahun lalu.
"""
from bankbench.matcher import evaluate_column

# (enumerator, label publikasi, baris template atau None, jenis) ; jenis: 'v' angka, 'h' judul/induk tanpa angka
BS = [
    ("1", "Kas", 8), ("2", "Penempatan pada Bank Indonesia", 9), ("3", "Penempatan pada bank lain", 10),
    ("4", "Tagihan spot dan derivatif/forward", 11), ("5", "Surat berharga yang dimiliki", 12),
    ("6", "Surat berharga yang dijual dengan janji dibeli kembali (repo)", 17),
    ("7", "Tagihan atas surat berharga yang dibeli dengan janji dijual kembali (reverse repo)", 18),
    ("8", "Tagihan akseptasi", 19), ("9", "Kredit yang diberikan", 24), ("10", "Pembiayaan syariah", 25),
    ("11", "Penyertaan modal", 26), ("12", "Aset keuangan lainnya", None),
    ("13", "Cadangan kerugian penurunan nilai aset keuangan -/-", "h"),
    ("a", "Surat berharga yang dimiliki", 28), ("b", "Kredit yang diberikan dan pembiayaan syariah", 29),
    ("c", "Lainnya", 30),
    ("14", "Aset tidak berwujud", 31), ("", "Akumulasi amortisasi aset tidak berwujud -/-", 32),
    ("15", "Aset tetap dan inventaris", 33), ("", "Akumulasi penyusutan aset tetap dan inventaris -/-", 34),
    ("16", "Aset non produktif", "h"), ("a", "Properti terbengkalai", 36), ("b", "Aset yang diambil alih", 37),
    ("c", "Rekening tunda", 38), ("d", "Aset antar kantor", 40),
    ("17", "Aset lainnya", 45), ("", "TOTAL ASET", 46),
    ("", "LIABILITAS DAN EKUITAS", "h"),
    ("1", "Giro", 51), ("2", "Tabungan", 52), ("3", "Deposito", 53), ("4", "Uang elektronik", None),
    ("5", "Liabilitas kepada Bank Indonesia", 55), ("6", "Liabilitas kepada bank lain", 56),
    ("7", "Liabilitas spot dan derivatif/forward", 57),
    ("8", "Liabilitas atas surat berharga yang dijual dengan janji dibeli kembali (repo)", 58),
    ("9", "Liabilitas akseptasi", 59), ("10", "Surat berharga yang diterbitkan", 60),
    ("11", "Pinjaman/pembiayaan yang diterima", 63), ("12", "Setoran jaminan", 64),
    ("13", "Liabilitas antar kantor", 66), ("14", "Liabilitas lainnya", 69), ("", "TOTAL LIABILITAS", 71),
    ("", "EKUITAS", "h"),
    ("15", "Modal disetor", "h"), ("a", "Modal dasar", 74), ("b", "Modal yang belum disetor -/-", 75),
    ("c", "Saham yang dibeli kembali (treasury stock) -/-", 76),
    ("16", "Tambahan modal disetor", "h"), ("a", "Agio", 78), ("b", "Disagio -/-", 79),
    ("c", "Dana setoran modal", 81), ("d", "Lainnya", 82),
    ("17", "Penghasilan komprehensif lain", 83),
    ("18", "Cadangan", "h"), ("a", "Cadangan umum", 98), ("b", "Cadangan tujuan", 99),
    ("19", "Laba/rugi", "h"), ("a", "Tahun-tahun lalu", 101), ("b", "Tahun berjalan", 102),
    ("c", "Dividen yang dibayarkan -/-", None),
    ("", "TOTAL EKUITAS YANG DAPAT DIATRIBUSIKAN KEPADA PEMILIK", 103),
    ("20", "Kepentingan non pengendali", 104), ("", "TOTAL EKUITAS", 105),
    ("", "TOTAL LIABILITAS DAN EKUITAS", 106),
]
IS = [
    ("A", "Pendapatan dan Beban Bunga", "h"), ("1", "Pendapatan Bunga", 116), ("2", "Beban Bunga", 120),
    ("", "Pendapatan (Beban) Bunga Bersih", 124),
    ("B", "Pendapatan dan Beban Operasional Lainnya", "h"),
    ("1", "Keuntungan (kerugian) dari peningkatan (penurunan) nilai wajar aset keuangan", 128),
    ("2", "Keuntungan (kerugian) dari penurunan (peningkatan) nilai wajar liabilitas keuangan", 133),
    ("3", "Keuntungan (kerugian) dari penjualan aset keuangan", 134),
    ("4", "Keuntungan (kerugian) dari transaksi spot dan derivatif/forward (realised)", 138),
    ("5", "Keuntungan (kerugian) dari penyertaan dengan equity method", 139),
    ("6", "Keuntungan (kerugian) dari penjabaran transaksi valuta asing", None),
    ("7", "Pendapatan dividen", 140), ("8", "Komisi/provisi/fee dan administrasi", 141),
    ("9", "Pendapatan lainnya", 143), ("10", "Kerugian penurunan nilai aset keuangan (impairment)", 158),
    ("11", "Kerugian terkait risiko operasional", 163), ("12", "Beban tenaga kerja", 167),
    ("13", "Beban promosi", 168), ("14", "Beban lainnya", 169),
    ("", "LABA (RUGI) OPERASIONAL", 172),
    ("", "PENDAPATAN DAN BEBAN NON OPERASIONAL", "h"),
    ("1", "Keuntungan (kerugian) penjualan aset tetap dan inventaris", 175),
    ("2", "Pendapatan (beban) non operasional lainnya", 177),
    ("", "LABA (RUGI) NON OPERASIONAL", 178),
    ("", "LABA (RUGI) PERIODE BERJALAN SEBELUM PAJAK", 180),
    ("", "Pajak penghasilan", "h"), ("a", "Taksiran pajak periode berjalan -/-", 184),
    ("b", "Pendapatan (beban) pajak tangguhan", 185),
    ("", "LABA (RUGI) PERIODE BERJALAN SETELAH PAJAK BERSIH", 187),
    ("1", "Pos-pos yang tidak akan direklasifikasi ke laba rugi", "h"),
    ("a", "Keuntungan revaluasi aset tetap", 195), ("b", "Pengukuran kembali atas program imbalan pasti", 197),
    ("2", "Pos-pos yang akan direklasifikasi ke laba rugi", "h"),
    ("a", "Selisih kurs penjabaran laporan keuangan dalam mata uang asing", 190),
    ("b", "Keuntungan (kerugian) dari perubahan nilai aset keuangan instrumen utang", 192),
    ("", "TOTAL LABA KOMPREHENSIF TAHUN BERJALAN", 201),
    ("", "Laba tahun berjalan yang dapat diatribusikan kepada :", "h"),
    ("", "PEMILIK", 204), ("", "KEPENTINGAN NON PENGENDALI", 205), ("", "TOTAL LABA TAHUN BERJALAN", 206),
    ("", "Total penghasilan komprehensif yang dapat diatribusikan kepada :", "h"),
    ("", "PEMILIK", 209), ("", "KEPENTINGAN NON PENGENDALI", 210),
    ("", "TOTAL LABA KOMPREHENSIF TAHUN BERJALAN", 211),
    ("", "DIVIDEN", 215), ("", "LABA BERSIH PER SAHAM", 217),
]
CAP = [
    ("I", "MODAL INTI (TIER 1)", 292), ("1", "Modal Inti Utama (CET 1)", "h"),
    ("1.1", "Modal disetor (Setelah dikurangi Treasury Stock)", 293), ("1.2", "Cadangan Tambahan Modal", 294),
    ("1.3", "Faktor Pengurang Modal Inti", 319), ("2", "Modal Inti Tambahan (AT 1)", None),
    ("II", "MODAL PELENGKAP (TIER 2)", 328), ("", "TOTAL MODAL", 350),
    ("", "ASET TERTIMBANG MENURUT RISIKO", "h"),
    ("", "ATMR RISIKO KREDIT", 352), ("", "ATMR RISIKO PASAR", 354), ("", "ATMR RISIKO OPERASIONAL", 353),
]
COMMIT = [
    ("1", "Fasilitas kredit kepada nasabah yang belum ditarik", None),
    ("2", "Irrevocable L/C yang masih berjalan", None), ("3", "Garansi yang diberikan", None),
]


def _fmt(v):
    if v is None:
        return "-"
    v = round(v)
    if v == 0:
        return "-"
    s = f"{abs(v):,}".replace(",", ".")
    return f"({s})" if v < 0 else s


def build_report_lines(model, cur_col, bs_comp_col, is_comp_col, bank_name="PT BANK CENTRAL ASIA Tbk",
                       period_text="30 September 2025", bs_comp_text="31 Desember 2024",
                       is_comp_text="30 September 2024"):
    """-> (list of (section, lines), expected {row: value}) ; lines sudah berisi angka terformat."""
    rows_by_num = {r.row: r for r in model.rows}

    def col_values(col):
        vals = evaluate_column(model, col, col, {})
        for r in model.rows:
            v = r.numeric(col)
            if v is not None and r.row not in vals:
                vals[r.row] = v
        return vals

    cur, bs_prev, is_prev = col_values(cur_col), col_values(bs_comp_col), col_values(is_comp_col)
    expected = {}
    blocks = []

    def block(title, spec, prev, comp_text, commit=False):
        lines = [bank_name, title, f"Per {period_text} dan {comp_text}", "(dalam jutaan rupiah)",
                 "BANK KONSOLIDASIAN", f"POS-POS {period_text} {comp_text} {period_text} {comp_text}"]
        k = 0
        for enum, label, row in spec:
            prefix = f"{enum}. " if enum else ""
            if row == "h":
                lines.append(prefix + label)
                continue
            if commit:
                k += 1
                vals = [1000 * k + 7, 900 * k + 3, 1000 * k + 11, 900 * k + 5]
            else:
                c = cur.get(row) if row else None
                p = prev.get(row) if row else None
                if row and row in rows_by_num and not rows_by_num[row].is_formula_at(cur_col) and c is not None:
                    expected[row] = c
                vals = [None if c is None else c * 0.95, None if p is None else p * 0.95, c, p]
            lines.append(prefix + label + " " + " ".join(_fmt(v) for v in vals))
        blocks.append(lines)

    block("LAPORAN POSISI KEUANGAN", BS, bs_prev, bs_comp_text)
    block("LAPORAN LABA RUGI DAN PENGHASILAN KOMPREHENSIF LAIN", IS, is_prev, is_comp_text)
    block("LAPORAN KOMITMEN DAN KONTINJENSI", COMMIT, None, bs_comp_text, commit=True)
    block("LAPORAN PERHITUNGAN KEWAJIBAN PENYEDIAAN MODAL MINIMUM (KPMM)", CAP, is_prev, is_comp_text)
    return blocks, expected


def write_pdf(blocks, path, two_columns=False):
    from reportlab.lib.pagesizes import A3, A4, landscape
    from reportlab.pdfgen import canvas

    size = landscape(A3) if two_columns else A4
    c = canvas.Canvas(str(path), pagesize=size)
    w, h = size
    font = 6.5 if two_columns else 7
    if two_columns:
        # Neraca kiri, Laba rugi kanan (seperti iklan di koran); sisanya halaman berikut
        pages = [blocks[:2], blocks[2:]]
        for page_blocks in pages:
            for i, lines in enumerate(page_blocks):
                x0 = 20 + i * (w / 2)
                y = h - 30
                for line in lines:
                    c.setFont("Helvetica", font)
                    c.drawString(x0, y, line)
                    y -= font + 3
            c.showPage()
    else:
        for lines in blocks:
            y = h - 40
            for line in lines:
                if y < 40:
                    c.showPage()
                    y = h - 40
                c.setFont("Helvetica", font)
                c.drawString(30, y, line)
                y -= font + 4
            c.showPage()
    c.save()


def write_xlsx(blocks, path):
    import openpyxl

    from bankbench.source_parser import split_label_values

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Publikasi"
    for lines in blocks:
        for line in lines:
            token, label, values = split_label_values(line)
            if values and label and not label.startswith("POS-POS"):
                ws.append([token or None, label] + values)
            else:
                ws.append([None, line])
        ws.append([])
    wb.save(path)
