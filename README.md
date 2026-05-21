# 🎵 Sistem Pemesanan Tiket Konser Terdistribusi — Nawa Sena

## Deskripsi Singkat
Proyek ini adalah simulasi penuh sistem pemesanan tiket konser menggunakan Python murni.
Dalam skenario ini, tiket konser **Nawa Sena** diperebutkan oleh user dummy:
- `Rian`
- `Dina`
- `Citra`
- `Sakti`

Semua mekanisme materi Week 9 sampai Week 13 dikombinasikan untuk menghasilkan bukti log terminal yang jelas.

## Ringkasan W9-W13
| Minggu | Materi | Implementasi | Log Terminal |
|---|---|---|---|
| **Week 9** | Fault Tolerance | Simulasi transient fault + Safe Retry | `[W9 - FAULT TOLERANCE] Koneksi putus, mencoba Retry ke-X...` |
| **Week 9** | Fault Tolerance | Replikasi Primary → Backup DB | `[W9 - REPLICATION] Data disalin ke Backup DB.` |
| **Week 10** | Asynchronous Programming | `asyncio` menangani request user serentak | `[W10 - ASYNC] Memulai request dari X user secara bersamaan...` |
| **Week 11** | Synchronization | `threading.Lock()`, Lamport Clock, Idempotency | `[W11 - IDEMPOTENCY] Duplikat request terdeteksi, saldo aman tidak terpotong dua kali.` |
| **Week 12** | Concurrency | `ThreadPoolExecutor` untuk email background | `[W12 - CONCURRENCY] E-Ticket dikirim ke email via background thread...` |
| **Week 13** | Multiprocessing | `multiprocessing.Pool` untuk generate QR Code | `[W13 - MULTIPROCESSING] Generate QR Code secara paralel di CPU memakan waktu X detik.` |

## Struktur Project
```text
files/
├── main.py
├── ticket_server.py
├── client.py
├── lamport_clock.py
├── idempotency.py
└── README.md
```

## Penjelasan File
- `main.py`: Entry point; menjalankan simulasi async dan multiprocessing.
- `ticket_server.py`: Server dengan replikasi Primary/Backup, mutex, Lamport Clock, idempotency, dan worker email.
- `client.py`: Client async yang melakukan safe retry dan double submit.
- `lamport_clock.py`: Logika Lamport Clock untuk event ordering.
- `idempotency.py`: Store idempotency untuk menghindari duplicate processing.

## Skenario Demo
1. `Rian` melakukan **double-submit** untuk tiket yang sama.
2. `Dina`, `Citra`, dan `Sakti` juga meminta tiket serentak.
3. Sistem melakukan **retry** ketika koneksi putus.
4. Data pembelian disalin ke **Backup DB**.
5. Email dikirim dengan thread background.
6. Setelah selesai, QR Code dibuat secara paralel dengan multiprocessing.

## Cara Menjalankan
Buka terminal pada folder `files` lalu jalankan:
```bash
python main.py
```

## Output yang Diharapkan
- Log W9 - W13 muncul lengkap di terminal.
- Terdapat bukti retry, replikasi, idempotency, concurrency, dan multiprocessing.
- Hasil akhir menunjukkan siapa yang berhasil mendapatkan tiket.
