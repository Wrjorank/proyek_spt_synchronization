# 🎵 Concert Ticket Booking System
## SPT Project — Week 11: Synchronization

---

## 📌 Deskripsi

Simulasi sistem pemesanan tiket konser yang mengimplementasikan konsep-konsep
**Synchronization** dari mata kuliah Sistem dan Pemrograman Terdistribusi (SPT).

---

## 🧠 Konsep yang Diimplementasikan

| Konsep | File | Penjelasan |
|---|---|---|
| **Race Condition** | `main.py` (Skenario 1) | Demo bug ketika tiket bisa terjual ke banyak orang |
| **Mutex Lock** | `ticket_server.py` | Mencegah race condition dengan mutual exclusion |
| **Lamport Clock** | `lamport_clock.py` | Mengurutkan event secara logis tanpa physical time |
| **Idempotency** | `idempotency.py` | Mencegah duplikasi transaksi saat request dikirim ulang |
| **Concurrent Clients** | `client.py` | Simulasi banyak user (thread) membeli bersamaan |

---

## 📁 Struktur Project

```
concert_ticket_system/
├── main.py            # Entry point, semua skenario demo
├── ticket_server.py   # Server dengan mutex lock & event log
├── lamport_clock.py   # Implementasi Lamport Clock
├── idempotency.py     # Safe retry mechanism
├── client.py          # Simulasi concurrent users
└── README.md
```

---

## ▶️ Cara Menjalankan

### Requirements
- Python 3.10+ (tidak perlu install library eksternal)

### Run
```bash
cd concert_ticket_system
python main.py
```

---

## 🎬 Skenario Demo

### Skenario 1 — Race Condition (Tanpa Sinkronisasi)
- 5 user berebut 1 tiket secara bersamaan
- Tanpa lock → tiket bisa terjual ke lebih dari 1 orang
- Ini adalah **bug yang disengaja** untuk menunjukkan pentingnya sinkronisasi

### Skenario 2 — Mutex Lock (Dengan Sinkronisasi)
- 10 user berebut 1 tiket
- Dengan `threading.Lock()` → hanya 1 user yang berhasil
- Sisanya mendapat notifikasi tiket habis

### Skenario 3 — Idempotency
- 1 user mengirim request beli tiket yang sama sebanyak 3x (simulasi retry)
- Sistem mendeteksi duplikasi via `idempotency_key`
- Tiket tetap terhitung terjual **1x saja**

### Skenario 4 — Lamport Clock
- 15 user beli tiket bersamaan
- Setiap event diberi **logical timestamp** oleh Lamport Clock
- Event log ditampilkan terurut berdasarkan kausalitas, bukan waktu fisik

### Skenario 5 — Full Load Test
- 50 user berebut 15 tiket
- Statistik akhir: berhasil, gagal, duplicate

---

## 🔑 Bagian Kode Penting

### Mutex Lock — Critical Section
```python
# ticket_server.py
self._mutex = threading.Lock()

if self.use_sync:
    self._mutex.acquire()   # LOCK 🔒
try:
    result = self._process_purchase(user_id, ticket_id, recv_ts)
finally:
    if self.use_sync:
        self._mutex.release()  # UNLOCK 🔓
```

### Lamport Clock — Receive Rule
```python
# lamport_clock.py
def receive(self, received_time: int) -> int:
    with self._lock:
        self.time = max(self.time, received_time) + 1
        return self.time
```

### Idempotency — Safe Retry
```python
# idempotency.py
idem_key = generate_idempotency_key(user_id, ticket_id)
if self._idem_store.is_processed(idem_key):
    cached = self._idem_store.get_result(idem_key)
    return cached_result  # Kembalikan hasil lama, jangan proses ulang
```

---

## 👥 Tim

- [Wahyu Rizky F Simanjorang]
- [Raynal Haposan Napitupulu]
- [Michael Saragih]

---

## 📚 Referensi

- Tanenbaum, A. S., & Van Steen, M. — *Distributed Systems: Principles and Paradigms*
- Materi SPT Week 11: Synchronization (Chandro Pardede, 2026)
- Lamport, L. (1978). *Time, Clocks, and the Ordering of Events in a Distributed System*
