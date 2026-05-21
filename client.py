"""
Client - Simulasi banyak user membeli tiket secara bersamaan
Week 11: Synchronization - SPT Project
"""

import threading
import time
import random
from lamport_clock import LamportClock
from ticket_server import TicketServer, PurchaseResult


class TicketClient:
    """
    Simulasi satu user yang mencoba membeli tiket.
    Setiap client punya Lamport Clock sendiri (layaknya node berbeda).
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.clock = LamportClock(user_id)
        self.results: list[PurchaseResult] = []

    def buy_ticket(self, server: TicketServer, ticket_id: str):
        """Kirim request pembelian ke server."""
        send_ts = self.clock.send()
        result = server.purchase_ticket(self.user_id, ticket_id, client_clock=send_ts)
        self.clock.receive(result.timestamp)
        self.results.append(result)
        return result

    def buy_ticket_with_retry(self, server: TicketServer, ticket_id: str, retries: int = 3):
        """
        Simulasi jaringan tidak stabil → client retry beberapa kali.
        Berkat idempotency, tidak ada duplikasi meskipun request dikirim ulang.
        """
        for attempt in range(1, retries + 1):
            send_ts = self.clock.send()
            result = server.purchase_ticket(self.user_id, ticket_id, client_clock=send_ts)
            self.clock.receive(result.timestamp)
            self.results.append(result)

            if result.is_duplicate:
                print(f"  [{self.user_id}] Retry #{attempt}: {result.message}")
            else:
                break

            time.sleep(0.1)  # Jeda antar retry

        return result


# ─────────────────────────────────────────────
#  Helper: Jalankan banyak client secara concurrent
# ─────────────────────────────────────────────

def simulate_concurrent_purchases(server: TicketServer,
                                  user_ticket_pairs: list[tuple[str, str]],
                                  label: str = "Simulasi") -> list[dict]:
    """
    Jalankan banyak pembelian tiket secara bersamaan menggunakan threads.
    Setiap thread = satu user = satu client node.
    """
    results = []
    results_lock = threading.Lock()
    threads = []

    def worker(user_id: str, ticket_id: str):
        client = TicketClient(user_id)
        # Tambah jitter kecil agar tidak semua mulai bersamaan persis
        time.sleep(random.uniform(0, 0.05))
        result = client.buy_ticket(server, ticket_id)
        with results_lock:
            results.append({
                "user": user_id,
                "ticket": ticket_id,
                "success": result.success,
                "message": result.message,
                "lamport_ts": result.timestamp,
                "duplicate": result.is_duplicate
            })

    print(f"\n{'─'*60}")
    print(f"  🎫 {label}")
    print(f"  {len(user_ticket_pairs)} request dikirim secara bersamaan...")
    print(f"{'─'*60}")

    start = time.time()

    for user_id, ticket_id in user_ticket_pairs:
        t = threading.Thread(target=worker, args=(user_id, ticket_id))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start

    # Tampilkan hasil
    results.sort(key=lambda x: x["lamport_ts"])
    for r in results:
        icon = "✅" if r["success"] else ("🔁" if r["duplicate"] else "❌")
        print(f"  {icon} [{r['lamport_ts']:>3}] {r['user']:<12} → {r['message']}")

    print(f"\n  ⏱  Selesai dalam {elapsed:.2f} detik")
    return results
