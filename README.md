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
     4. *Penyeimbang Laba Rugi* — akun baru di laporan (mis. "Pendapatan Asuransi - Neto") yang persis
        menutup selisih LABA OPERASIONAL / NON OPERASIONAL / TOTAL LABA KOMPREHENSIF dimasukkan ke
        Pendapatan/Beban lainnya (atau "Lainnya" di penghasilan komprehensif).
     5. *Turunan total* — kalau angka satu akun tidak terbaca (mis. OCR), nilainya dihitung dari total
        laporan (mis. Beban bunga = Pendapatan bunga − Pendapatan bunga bersih), dicek wajar vs periode lalu.
     Rasio yang koma desimalnya hilang (mis. OCR "446" untuk 4,46) disesuaikan ke skala periode acuan.
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
   dengan satu akun laporan diberi keterangan. Status **KLASIFIKASI** = angkanya sudah benar, hanya
   dikelompokkan berbeda (mis. minority interest di Ekuitas template, di Liabilitas laporan).
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
| `bankbench/banks.py` | Deteksi bank dari laporan (angka histori, judul "PT Bank …", teks, nama file) |
| `bankbench/crosscheck.py` | Cek silang NPL ÷ total kredit vs rasio NPL gross |
| `bankbench/persist.py` | Simpan memori pola permanen ke repo GitHub (Streamlit Cloud) |
| `bankbench/regress.py` | Regresi dengan laporan asli di `tests/regression` |

## Test

```bash
python -m pytest -q            # termasuk end-to-end dengan template asli (~40 detik)
python -m pytest -q -m "not slow"
python -m pytest -q -m regression   # 11 laporan publikasi asli → harus 0 defect (beberapa menit, OCR)
python -m bankbench.regress         # sama, dengan ringkasan per laporan
```

**Defect** = cek total yang BEDA + baris wajib isi yang kosong. Laporan asli ada di
`tests/regression/reports/`, daftarnya di `tests/regression/manifest.json` — tambahkan laporan bank
baru di situ supaya setiap perubahan kode diuji ulang ke semua bank.

## Diuji dengan laporan asli

| Laporan | Format | Catatan |
|---|---|---|
| BCA Des 2025 | PDF teks (spasi "hantu" di dalam angka) | Neraca seimbang; LR & KPMM cocok; NPL & rasio terisi |
| Mandiri Q4 2025 | 1 halaman koran, 3 kolom | Angka 2024 di-restate Mandiri → Pendapatan/Beban bunga diisi dari nama akun (🟡 CEK) |
| Mandiri Q2 2026 | 1 halaman koran, 2 "lantai" dengan kolom berbeda, baris miring | Terbaca penuh; Neraca Jun 26 memakai hasil Dec 25 sebagai acuan |
| Permata Jun 2026 | PDF teks | Kolom Dec 25 kosong → Neraca diisi dari nama akun, seimbang ke laporan; LR/KPMM/NPL/rasio ikut pola |
| BNI 1H 2026 | PDF teks, header bertumpuk & tabel berdampingan | Neraca seimbang (akun asuransi/kelompok lepasan ditempatkan otomatis), LR & KPMM cocok dengan laporan |
| BRI Des 2025 | PDF teks bahasa Inggris, angka 2024 di-restate (PSAK 117) | Neraca, Laba Rugi & KPMM cocok; nama akun Inggris & salah ketik ('Comissions', 'Deffered') dikenali |
| BNI Des 2025 | PDF teks, akun asuransi baru | Seimbang; akun asuransi & OCI baru ditempatkan otomatis; NPL terisi |
| OCBC NISP Des 2025 | Neraca & liabilitas berdampingan, judul berspasi per huruf, header hanya tahun | Semua total cocok; halaman Unit Usaha Syariah diabaikan; NPL terisi |
| BTN Des 2025 | PDF teks | Semua total cocok; AT 1 baru di KPMM ditempatkan otomatis |
| CIMB Niaga Des 2025 | PDF teks bahasa Inggris, header 'BANK CIMB NIAGA  CONSOLIDATED' | Semua total cocok; halaman Sharia Business Unit diabaikan |
| BSI Des 2025 | 1 halaman koran, huruf berupa gambar vektor (tanpa teks) | OCR per blok tabel: semua total cocok (Neraca, LR, KPMM, NPL, rasio); tabel grup Bank Mandiri di halaman sama dibuang |
| SMBC Indonesia Des 2025 | Tabel berupa gambar, bahasa Inggris | OCR + koreksi digit OCR yang diuji ke total: semua total cocok |

| Permata Des 2025 | PDF teks multi-halaman | Semua total cocok; jadi acuan berantai untuk Jun 2026 |
| Maybank Indonesia Des 2025 | PDF teks, 'spasi hantu' & sel '-' hilang di tabel kolektibilitas | Kolom kolektibilitas diperbaiki dari JUMLAH; rumus NPL tanpa pembagi dikenali |
| Panin Des 2025 | 1 halaman koran, tabel berdampingan + daftar pengurus di samping Laba Rugi | Varian layout kedua (dipilih otomatis dari skor kualitas); semua total cocok |
| Danamon Des 2025 | 1 halaman koran, angka 2024 di-restate | Diisi dari nama akun (🟡 CEK) dengan tanda mengikuti template; Neraca & LR cocok |

Hasil regresi terakhir: **0 defect di 16 laporan dari 13 bank** (`python -m bankbench.regress`).

## Catatan

- Kalau periode acuan belum terisi di template (mis. Dec 25 kosong saat mengisi Jun 26), Neraca
  tetap diisi lewat pengenalan akun (🟡 CEK). Untuk strict penuh, upload juga laporan periode
  acuannya — akan diproses lebih dulu.
- openpyxl tidak menyimpan ulang chart/gambar di workbook; kalau template punya chart,
  salin sheet hasil update ke file aslimu.
- **Memori pola permanen** (`mappings.json`: pasangan manual + memori resep). Di Streamlit Cloud
  disk hilang saat restart, jadi isi *Settings → Secrets* app:

  ```toml
  [mappings_github]
  token  = "github_pat_..."   # fine-grained token, akses Contents read & write ke repo ini saja
  repo   = "owner/Bank-Quarterly-Benchmarking"
  branch = "main"             # opsional
  path   = "mappings.json"    # opsional
  ```

  Memori dibaca dari repo saat app mulai, dan tombol **💾 Simpan memori pola** menyimpannya lagi
  (digabung dengan isi repo, tidak menimpa). Tanpa secrets: download mappings.json lalu upload lagi
  di sesi berikutnya (expander *Memori pola*).

---

## IB Prep Studio (offline)

`ib-prep/index.html` is a standalone, offline study guide for breaking into investment banking:
recruiting roadmap, technical modules (accounting, EV, valuation, DCF, M&A, LBO, FIG), behavioral prep,
spaced-repetition flashcards, quizzes with explanations, pop-up quizzes, mental-math sprints and a prep
checklist. Download the file and open it in any browser; no internet or install needed. Progress is saved in
the browser's local storage.

The **Models** tab adds a three-statement simulator, DCF / LBO / VC & PE calculators, a study-resources list, and
four downloadable Excel practice templates with live formulas (also in `ib-prep/templates/`): three-statement
model, DCF, LBO, and a VC & PE toolkit (VC method, cap table, exit waterfall, fund waterfall). To regenerate them:

```bash
python ib-prep/build_templates.py           # writes ib-prep/templates/*.xlsx
python ib-prep/build_templates.py --embed   # embeds them into ib-prep/index.html
```
