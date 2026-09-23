# power2n

Homework HW1 — Menghitung `2**n` dengan 4 metode berbeda di Python.

## Cara menjalankan

```
python power2n.py
```

Hasil untuk `n = 100` diverifikasi sama dengan `2**100`.

## Metode yang diuji

| # | Fungsi | Implementasi | Kompleksitas | n=100 |
|---|--------|--------------|--------------|-------|
| 1 | `power2n_1` | `return 2**n` | O(1) | ✅ selesai |
| 2a | `power2n_2a` | `power2n_2a(n-1) + power2n_2a(n-1)` | O(2^n) | ❌ tidak selesai |
| 2b | `power2n_2b` | `2 * power2n_2b(n-1)` | O(n) | ✅ selesai |
| 3 | `power2n_3` | rekursi + tabel (`dict`) memoization | O(n) | ✅ selesai |

Catatan: `power2n_3` memakai `power2n_3(n-1) + power2n_3(n-1)` yang sama seperti metode 2a, tetapi hasil tiap `n` disimpan di tabel, sehingga setiap `n` hanya dihitung satu kali → kompleksitas turun dari O(2^n) menjadi O(n).

## Hasil pengukuran (n = 100)

```
方法 1 (2**n):           結果正確 | 時間 = 0.000001 秒
方法 2b (2*power2n(n-1)): 結果正確 | 時間 = 0.000055 秒
方法 3 (遞迴+查表):       結果正確 | 時間 = 0.000038 秒
方法 2a (n-1)+(n-1):     n=100 -> 不結束 (5 秒 timeout)
```

## Kesimpulan

- Metode 1, 2b, dan 3 cepat dan benar untuk n=100.
- Metode 2a tidak feasibel: waktu tumbuh ~2x setiap n bertambah 1 (lihat pengujian n=15..25 pada output program). Untuk n=100 dibutuhkan ≈ 2^100 ≈ 1.27×10^30 operasi, sehingga program dijaga dengan timeout 5 detik.
- Rekursi kedalaman n=100 aman (limit Python default 1000), terbukti metode 2b maupun 3 berjalan mulus.