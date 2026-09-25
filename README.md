# Bank-Quarterly-Benchmarking

Web tool (Streamlit) untuk meng-update `template.xlsx` benchmarking bank dari
**laporan keuangan publikasi** (PDF / Excel). User cukup upload file, sistem yang:

1. **Mengenali bank** → sheet tujuan (dari nama bank + angka yang cocok dengan histori sheet).
2. **Mengenali periode** (mis. "30 September 2025" → kolom `Sep 25`).
3. **Membaca hanya 3 seksi**: Neraca (Balance Sheet), Laba Rugi (Income Statement),
   Struktur Modal (KPMM / Capital Adequacy). Komitmen & kontinjensi, kualitas aset, dll diabaikan.
4. **Mengidentifikasi akun** ke baris template:
   - *Pola angka*: angka pembanding di laporan (Des tahun lalu / kuartal yang sama tahun lalu)
     dicocokkan dengan histori template. Dari sini sistem tahu akunnya, kolom mana yang
     konsolidasian periode berjalan, skala (juta/miliar), dan konvensi tanda (+/-).
   - *Alias*: kamus padanan nama akun format OJK baru ↔ label template (`bankbench/aliases.py`
     + `mappings.json` hasil belajar dari koreksi user).
   - *Nama akun*: fuzzy matching + induk akun + urutan (untuk label kembar seperti "Lainnya").
5. **Validasi**: total di template (TOTAL ASET, LABA OPERASIONAL, Modal Inti, dst.) dihitung ulang
   dari angka baru dan dibandingkan dengan total di laporan, plus cek Aset = Liabilitas + Ekuitas.
6. **Menulis**: kolom periode diisi (kalau sudah ada, mis. `Dec 25` kosong) atau **ditambah**
   setelah kolom terakhir. Format & semua formula (termasuk rasio di bawahnya, ANNUALIZER,
   tanggal periode) ikut diperpanjang. Baris formula tidak ditimpa.

Baris yang di histori template **biasanya kosong** (mis. induk "Kredit" yang angkanya ditaruh
di sub-baris) tidak diisi otomatis supaya total tidak dobel.

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run main.py
```

Template: taruh file Excel dengan nama `template.xlsx` di root repo.

## Struktur kode

| File | Isi |
|---|---|
| `main.py` | UI Streamlit |
| `bankbench/template_model.py` | Membaca struktur sheet bank (seksi, baris akun, hirarki, histori) |
| `bankbench/source_parser.py` | Parser laporan PDF (termasuk layout 2 kolom) & Excel |
| `bankbench/matcher.py` | Identifikasi akun, deteksi kolom/skala/tanda, rekonsiliasi total |
| `bankbench/writer.py` | Menulis / menambah kolom periode ke workbook |
| `bankbench/aliases.py` | Kamus padanan nama akun + pemetaan hasil belajar |
| `bankbench/banks.py` | Deteksi bank dari laporan |

## Test

```bash
python -m pytest -q            # termasuk end-to-end dengan template asli (~30 detik)
python -m pytest -q -m "not slow"
```

Test end-to-end membuat laporan publikasi sintetis (format OJK, 4 kolom Bank/Konsolidasian)
dari angka yang ada di template, lalu memastikan sistem bisa merekonstruksi kolom tersebut.

## Catatan

- PDF hasil scan (gambar) tidak bisa dibaca — pakai PDF teks atau Excel dari website bank / OJK.
- openpyxl tidak menyimpan ulang chart/gambar di workbook; kalau template punya chart,
  salin sheet hasil update ke file aslimu.
- Pemetaan hasil koreksi bisa di-download sebagai `mappings.json`; commit ke repo supaya permanen.
