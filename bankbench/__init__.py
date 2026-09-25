"""Engine untuk auto-update template benchmarking bank dari laporan publikasi.

Modul:
- text            : normalisasi label akun, similarity, parsing angka
- periods         : parsing/format label periode (mis. 'Sep 25') & deteksi periode laporan
- template_model  : baca struktur sheet bank di template (seksi, baris akun, histori)
- source_parser   : baca laporan publikasi (PDF/Excel) -> baris akun + angka + seksi
- matcher         : identifikasi akun (alias, pola angka, nama akun) + validasi
- writer          : tulis/tambah kolom periode ke workbook
"""
