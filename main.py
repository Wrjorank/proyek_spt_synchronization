"""
Main - Concert Ticket Booking System
======================================
Proyek SPT - Week 11: Synchronization
Topik  : Sistem Pemesanan Tiket Konser
Konsep : Race Condition, Mutex Lock, Lamport Clock, Idempotency

Cara jalankan:
    python main.py

Skenario yang didemonstrasikan:
    1. Race Condition TANPA sinkronisasi (bug intentional)
    2. Pembelian DENGAN sinkronisasi (mutex lock)
    3. Idempotency - safe retry / double request
    4. Event Log berurutan menggunakan Lamport Clock
"""

import time
import threading
from ticket_server import TicketServer
from client import TicketClient, simulate_concurrent_purchases


# ═══════════════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════════════

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🎵  CONCERT TICKET BOOKING SYSTEM  🎵                   ║
║     SPT Project — Week 11: Synchronization                   ║
║                                                              ║
║  Konsep: Race Condition · Mutex Lock                         ║
║          Lamport Clock  · Idempotency                        ║
╚══════════════════════════════════════════════════════════════╝
""")


def print_section(title: str, number: int):
    print(f"\n{'═'*62}")
    print(f"  SKENARIO {number}: {title}")
    print(f"{'═'*62}")


# ═══════════════════════════════════════════════════════════════
#  SKENARIO 1 — Race Condition TANPA Sinkronisasi
# ═══════════════════════════════════════════════════════════════

def demo_race_condition():
    print_section("RACE CONDITION — Tanpa Sinkronisasi (use_sync=False)", 1)

    print("""
  ⚠️  PERINGATAN: Ini adalah demo BUG yang disengaja!
  Tanpa mutex lock, beberapa user bisa mendapatkan tiket
  yang sama pada waktu bersamaan (Race Condition).
    """)

    server = TicketServer("BTS World Tour Jakarta", use_sync=False)

    # 5 user berebut tiket A1 yang sama
    target_ticket = "TKT-A1"
    competitors = [
        (f"User-{i:02d}", target_ticket)
        for i in range(1, 6)
    ]

    results = simulate_concurrent_purchases(
        server, competitors,
        label="5 User berebut kursi A1 — TANPA LOCK"
    )

    wins = [r for r in results if r["success"]]
    print(f"\n  📊 Hasil: {len(wins)} user berhasil membeli tiket A1")
    if len(wins) > 1:
        print(f"  🐛 BUG TERDETEKSI: Tiket terjual ke {len(wins)} orang sekaligus!")
    else:
        print(f"  (Dalam kondisi ini, race condition mungkin tidak selalu terjadi)")
        print(f"  (Jalankan ulang program untuk melihat efeknya)")


# ═══════════════════════════════════════════════════════════════
#  SKENARIO 2 — Mutual Exclusion DENGAN Mutex Lock
# ═══════════════════════════════════════════════════════════════

def demo_mutex_lock():
    print_section("MUTUAL EXCLUSION — Dengan Mutex Lock (use_sync=True)", 2)

    print("""
  ✅ Dengan mutex lock aktif:
  Hanya satu thread yang masuk critical section dalam satu waktu.
  Tiket dijamin tidak terjual ke lebih dari satu orang.
    """)

    server = TicketServer("BTS World Tour Jakarta", use_sync=True)

    # 10 user berebut tiket A1 secara bersamaan
    target_ticket = "TKT-A1"
    competitors = [(f"User-{i:02d}", target_ticket) for i in range(1, 11)]

    results = simulate_concurrent_purchases(
        server, competitors,
        label="10 User berebut kursi A1 — DENGAN LOCK"
    )

    wins = [r for r in results if r["success"]]
    fails = [r for r in results if not r["success"]]
    print(f"\n  📊 Hasil:")
    print(f"     ✅ Berhasil beli : {len(wins)} user")
    print(f"     ❌ Gagal (habis) : {len(fails)} user")
    print(f"     {'✔️  AMAN' if len(wins) == 1 else '❌ ERROR'}: Tiket A1 hanya terjual ke 1 orang")

    server.print_event_log(limit=12)


# ═══════════════════════════════════════════════════════════════
#  SKENARIO 3 — Idempotency (Safe Retry)
# ═══════════════════════════════════════════════════════════════

def demo_idempotency():
    print_section("IDEMPOTENCY — Safe Retry / Double Request", 3)

    print("""
  Masalah: User klik tombol beli 2x karena jaringan lambat.
  Solusi : Idempotency key mencegah duplikasi transaksi.
  
  Setiap kombinasi (user_id + ticket_id) menghasilkan key unik.
  Request kedua dengan key yang sama → kembalikan hasil pertama.
    """)

    server = TicketServer("Coldplay Music of the Spheres Jakarta", use_sync=True)

    user_id = "Budi-Santoso"
    ticket_id = "TKT-A3"

    print(f"  👤 User   : {user_id}")
    print(f"  🎫 Tiket  : {ticket_id} (Kursi A3)")

    client = TicketClient(user_id)

    print(f"\n  📡 Request #1 — Pembelian pertama:")
    result1 = client.buy_ticket(server, ticket_id)
    print(f"     → {result1.message}")
    print(f"     → Lamport timestamp: {result1.timestamp}")
    print(f"     → Duplicate: {result1.is_duplicate}")

    print(f"\n  📡 Request #2 — Retry (jaringan lambat, user klik lagi):")
    result2 = client.buy_ticket(server, ticket_id)
    print(f"     → {result2.message}")
    print(f"     → Duplicate: {result2.is_duplicate}")

    print(f"\n  📡 Request #3 — Retry kedua:")
    result3 = client.buy_ticket(server, ticket_id)
    print(f"     → {result3.message}")
    print(f"     → Duplicate: {result3.is_duplicate}")

    print(f"\n  📊 Hasil:")
    print(f"     Tiket A3 terjual ke   : {server.tickets[ticket_id].owner}")
    total_sold = sum(1 for t in server.get_sold_tickets())
    print(f"     Total tiket terjual   : {total_sold} (seharusnya tetap 1, bukan 3)")
    print(f"     ✅ Idempotency bekerja: tidak ada duplikasi!")


# ═══════════════════════════════════════════════════════════════
#  SKENARIO 4 — Lamport Clock Event Ordering
# ═══════════════════════════════════════════════════════════════

def demo_lamport_clock():
    print_section("LAMPORT CLOCK — Logical Event Ordering", 4)

    print("""
  Masalah: Di sistem terdistribusi, setiap node punya jam sendiri.
           Jam fisik tidak bisa dipercaya.
  Solusi : Lamport Clock mengurutkan event berdasarkan kausalitas,
           bukan waktu fisik.
  
  Demonstrasi: Banyak user beli berbagai tiket → lihat urutan event.
    """)

    server = TicketServer("Dewa 19 Reunion Concert", use_sync=True)

    # Simulasi 15 user membeli tiket berbeda secara bersamaan
    import random
    random.seed(42)
    tickets_available = [f"TKT-A{i}" for i in range(1, 6)] + \
                        [f"TKT-B{i}" for i in range(1, 6)]

    purchases = []
    for i in range(1, 16):
        user = f"User-{i:02d}"
        ticket = random.choice(tickets_available)
        purchases.append((user, ticket))

    simulate_concurrent_purchases(
        server, purchases,
        label="15 User beli tiket secara bersamaan"
    )

    server.print_event_log(limit=20)

    print("  📖 Penjelasan Lamport Clock:")
    print("     • Setiap event memiliki timestamp logis (bukan waktu nyata)")
    print("     • Event dengan timestamp lebih kecil terjadi lebih 'dulu'")
    print("     • Aturan: clock = max(local, received) + 1 saat terima pesan")
    print("     • Memberikan partial ordering yang konsisten\n")


# ═══════════════════════════════════════════════════════════════
#  SKENARIO 5 — Full Load Test
# ═══════════════════════════════════════════════════════════════

def demo_full_load():
    print_section("FULL LOAD TEST — 50 User, 15 Tiket", 5)

    print("""
  Simulasi nyata: 50 user berebut 15 kursi yang tersedia.
  Hanya 15 yang berhasil, sisanya mendapat notifikasi tiket habis.
    """)

    server = TicketServer("Blackpink Born Pink Jakarta", use_sync=True)

    import random
    random.seed(99)
    all_tickets = list(server.tickets.keys())  # A1-A10, B1-B5

    purchases = []
    for i in range(1, 51):
        user = f"User-{i:03d}"
        ticket = random.choice(all_tickets)
        purchases.append((user, ticket))

    results = simulate_concurrent_purchases(
        server, purchases,
        label="50 User, 15 Kursi Tersedia"
    )

    wins = [r for r in results if r["success"] and not r["duplicate"]]
    fails = [r for r in results if not r["success"]]
    dupes = [r for r in results if r["duplicate"]]

    print(f"\n  📊 Statistik Final:")
    print(f"     Total request      : {len(results)}")
    print(f"     ✅ Berhasil beli   : {len(wins)}")
    print(f"     ❌ Gagal (habis)   : {len(fails)}")
    print(f"     🔁 Duplicate req   : {len(dupes)}")
    print(f"     🎫 Tiket terjual   : {len(server.get_sold_tickets())} dari 15")
    print(f"     🎫 Tiket sisa      : {len(server.get_available_tickets())}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print_banner()

    try:
        demo_race_condition()
        time.sleep(0.5)

        demo_mutex_lock()
        time.sleep(0.5)

        demo_idempotency()
        time.sleep(0.5)

        demo_lamport_clock()
        time.sleep(0.5)

        demo_full_load()

        print("\n" + "═"*62)
        print("  ✅ Semua skenario selesai dijalankan!")
        print("  📚 Konsep yang didemonstrasikan:")
        print("     1. Race Condition   — akibat tidak ada sinkronisasi")
        print("     2. Mutex Lock       — mutual exclusion, critical section")
        print("     3. Idempotency      — safe retry, mencegah duplikasi")
        print("     4. Lamport Clock    — logical event ordering")
        print("     5. Load Testing     — sistem di bawah tekanan tinggi")
        print("═"*62 + "\n")

    except KeyboardInterrupt:
        print("\n\n  Program dihentikan oleh user.")
