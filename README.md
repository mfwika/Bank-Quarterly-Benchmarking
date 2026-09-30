# Bank-Quarterly-Benchmarking

Web tool (Streamlit) untuk meng-update `template.xlsx` benchmarking bank dari
**laporan keuangan publikasi** (PDF / Excel). User cukup upload file (boleh beberapa bank
& beberapa periode sekaligus), sistem yang:

1. **Mengenali bank** → sheet tujuan (nama bank + angka yang cocok dengan histori sheet).
2. **Mengenali periode** tiap file (mis. "30 Juni 2026" → kolom `Jun 26`).
3. **Membaca** Neraca, Laba Rugi, KPMM (struktur modal), tabel Rasio Keuangan, dan tabel
   Kualitas Aset Produktif (kolektibilitas L/DPK/KL/D/M) — lengkap dengan header kolomnya
   (periode + Individual/Konsolidasian).
4. **Mengisi dengan mode STRICT — meniru pola periode acuan**:

   | Baris template | Periode acuan pola |
   |---|---|
   | Neraca | **Desember tahun lalu** (minta Jun 26 → lihat Dec 25) |
   | Laba Rugi, KPMM, Rasio, NPL | **periode yang sama tahun lalu** (minta Jun 26 → lihat Jun 25) |

   - Nilai template di periode acuan dicari di angka **pembanding** laporan: satu akun, atau
     **jumlah 2–4 akun** (mis. "Aset lainnya" = Aset lainnya + Aset keuangan lainnya).
   - Resep yang sama diterapkan ke angka periode berjalan. Hasil penjumlahan ditulis sebagai
     rumus (`=a+b`) seperti gaya analis, supaya rinciannya kelihatan.
   - **Pola tidak tersedia → akun tetap dikenali** (ditandai 🟡 **CEK**), berlapis:
     1. *Memori pola* — resep bank ini dari periode sebelumnya (`_recipes`).
     2. *Nama akun* — nama/kamus padanan + posisi baris, dicek wajar vs periode lalu (0,1×–10×);
        ditambah *kebiasaan penjumlahan* (mis. Aset lainnya + Aset keuangan lainnya) yang dipelajari
        dari resep bank lain (`_conventions`); akun `-/-` ditulis negatif sesuai konvensi template.
     3. *Penyeimbang Neraca* — akun laporan yang belum terpakai dikenali **sisinya** dari posisinya
        di laporan (sebelum TOTAL ASET = aset, sebelum TOTAL LIABILITAS = liabilitas, sesudahnya =
        ekuitas). Kombinasi akun yang jumlahnya persis menutup selisih TOTAL ASET / JUMLAH LIABILITAS
        DAN EKUITAS dimasukkan ke baris template yang namanya cocok, atau ke Aset/Liabilitas/Ekuitas lainnya.
     Ini berlaku saat kolom acuan kosong (mis. Dec 25 belum diisi) atau angka pembanding di-restate.
     Yang tetap tidak dikenali → dikosongkan & ditandai ⚠.
   - Baris yang kosong di periode acuan tidak diisi, kecuali akun barunya diperlukan supaya Neraca
     sama dengan laporan (lapis penyeimbang di atas); selain itu muncul peringatan "akun baru?".
   - Entitas: Neraca/Laba Rugi/KPMM → **Konsolidasian** (kecuali judul seksi template "Bank");
     Rasio & NPL → ikut kolom yang cocok di periode acuan (biasanya Bank only).
   - **NPL** (Current / Special Mention / NPL): tiap komponen rumus acuan, mis.
     `=(129452+10588078+…)/1000`, dilacak ke sel tabel kualitas aset (baris + kolektibilitas),
     lalu ditulis rumus baru dengan susunan & pembagi yang sama.
   - Kalau di periode acuan sel berupa **rumus** (mis. LDR `=((I24+I25+I43)/…)*100`), rumus itu
     yang digeser ke kolom tujuan.
5. **Berantai & belajar**: file bank yang sama diproses dari periode lama ke baru (hasil Dec 25
   langsung jadi acuan Jun 26). Resep penjumlahan disimpan sebagai **memori pola**
   (`mappings.json` → `_recipes`), jadi akun yang sempat bernilai 0 di periode acuan tetap ikut.
6. **Validasi**: total template (TOTAL ASET, LABA OPERASIONAL, Modal Inti, …) dihitung ulang
   dan dibandingkan dengan laporan + cek Aset = Liabilitas + Ekuitas; selisih yang persis sama
   dengan satu akun laporan diberi keterangan (akun baru / beda klasifikasi).
7. **Menulis**: kolom periode diisi atau **ditambah**; format & semua formula (rasio turunan,
   ANNUALIZER, tanggal periode) ikut diperpanjang.

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run main.py
```

Template: taruh file Excel dengan nama `template.xlsx` di root repo. PDF berupa gambar dibaca
dengan OCR (Tesseract; `packages.txt` untuk Streamlit Cloud).

## Struktur kode

| File | Isi |
|---|---|
| `main.py` | UI Streamlit (per file: bank, periode, review, cek total; generate) |
| `bankbench/pattern.py` | **Mode strict**: periode acuan, resep (1–4 akun), rasio, NPL, memori resep |
| `bankbench/template_model.py` | Struktur sheet bank (seksi, hirarki akun, histori, baris rasio & NPL) |
| `bankbench/source_parser.py` | Parser PDF (layout koran multi-kolom, header kolom, OCR) & Excel |
| `bankbench/matcher.py` | Utilitas pencocokan nama/alias, evaluasi formula & rekonsiliasi total |
| `bankbench/writer.py` | Menulis / menambah kolom periode ke workbook |
| `bankbench/aliases.py` | Kamus padanan nama akun (ID/EN) + pemetaan hasil belajar |
| `bankbench/banks.py` | Deteksi bank dari laporan |

## Test

```bash
python -m pytest -q            # termasuk end-to-end dengan template asli (~40 detik)
python -m pytest -q -m "not slow"
```

## Diuji dengan laporan asli

| Laporan | Format | Catatan |
|---|---|---|
| BCA Des 2025 | PDF teks (spasi "hantu" di dalam angka) | Neraca seimbang; LR & KPMM cocok; NPL & rasio terisi |
| Mandiri Q4 2025 | 1 halaman koran, 3 kolom | Angka 2024 di-restate Mandiri → Pendapatan/Beban bunga diisi dari nama akun (🟡 CEK) |
| Mandiri Q2 2026 | 1 halaman koran, 2 "lantai" dengan kolom berbeda, baris miring | Terbaca penuh; Neraca Jun 26 memakai hasil Dec 25 sebagai acuan |
| Permata Jun 2026 | PDF teks | Kolom Dec 25 kosong → Neraca diisi dari nama akun, seimbang ke laporan; LR/KPMM/NPL/rasio ikut pola |
| BNI 1H 2026 | PDF teks, header bertumpuk & tabel berdampingan | Neraca seimbang (akun asuransi/kelompok lepasan ditempatkan otomatis), LR & KPMM cocok dengan laporan |
| SMBC Indonesia Des 2025 | Tabel berupa gambar, bahasa Inggris | Dibaca via OCR; perlu review |

## Catatan

- Kalau periode acuan belum terisi di template (mis. Dec 25 kosong saat mengisi Jun 26), Neraca
  tetap diisi lewat pengenalan akun (🟡 CEK). Untuk strict penuh, upload juga laporan periode
  acuannya — akan diproses lebih dulu.
- openpyxl tidak menyimpan ulang chart/gambar di workbook; kalau template punya chart,
  salin sheet hasil update ke file aslimu.
- `mappings.json` (pasangan manual + memori resep) bisa di-download dari app; commit ke repo
  supaya permanen.
