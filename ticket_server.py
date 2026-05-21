"""
Ticket Server - Inti dari sistem pemesanan tiket konser
Week 11: Synchronization - SPT Project

Konsep yang diimplementasikan:
- Mutex Lock       : Mencegah race condition (mutual exclusion)
- Lamport Clock    : Mengurutkan event secara logis
- Idempotency      : Safe retry, mencegah duplikasi pembelian
"""

import threading
import time
import random
from lamport_clock import LamportClock
from idempotency import IdempotencyStore, generate_idempotency_key


# ─────────────────────────────────────────────
#  Data model sederhana
# ─────────────────────────────────────────────

class Ticket:
    def __init__(self, ticket_id: str, seat: str, price: int):
        self.ticket_id = ticket_id
        self.seat = seat
        self.price = price
        self.is_available = True
        self.owner: str | None = None

    def __repr__(self):
        status = f"sold to {self.owner}" if self.owner else "available"
        return f"Ticket({self.seat}, {status})"


class PurchaseResult:
    def __init__(self, success: bool, message: str, ticket: Ticket | None = None,
                 timestamp: int = 0, is_duplicate: bool = False):
        self.success = success
        self.message = message
        self.ticket = ticket
        self.timestamp = timestamp
        self.is_duplicate = is_duplicate


# ─────────────────────────────────────────────
#  Ticket Server
# ─────────────────────────────────────────────

class TicketServer:
    """
    Server yang mengelola penjualan tiket konser.

    Race Condition Demo:
        Tanpa lock → banyak user bisa dapat tiket yang sama.
        Dengan lock → hanya satu user yang berhasil per tiket.
    """

    SERVER_ID = "TicketServer-1"

    def __init__(self, concert_name: str, use_sync: bool = True):
        self.concert_name = concert_name
        self.use_sync = use_sync                      # Toggle sync on/off untuk demo

        # Inisialisasi tiket (kursi A1 - A10, B1 - B5)
        self.tickets: dict[str, Ticket] = {}
        self._init_tickets()

        # Synchronization tools
        self._mutex = threading.Lock()                # Kunci utama (mutual exclusion)
        self._clock = LamportClock(self.SERVER_ID)
        self._idem_store = IdempotencyStore()

        # Log semua event
        self.event_log: list[dict] = []
        self._log_lock = threading.Lock()

    # ── Setup ──────────────────────────────────

    def _init_tickets(self):
        seats = [f"A{i}" for i in range(1, 11)] + [f"B{i}" for i in range(1, 6)]
        for seat in seats:
            tid = f"TKT-{seat}"
            self.tickets[tid] = Ticket(tid, seat, 500_000 if seat.startswith("A") else 350_000)

    # ── Logging ────────────────────────────────

    def _log(self, event_type: str, details: dict):
        ts = self._clock.tick()
        entry = {"lamport_ts": ts, "event": event_type, **details}
        with self._log_lock:
            self.event_log.append(entry)
        return ts

    # ── Core: Beli Tiket ───────────────────────

    def purchase_ticket(self, user_id: str, ticket_id: str,
                        client_clock: int = 0) -> PurchaseResult:
        """
        Proses pembelian tiket oleh seorang user.

        Parameter:
            user_id     : ID pembeli
            ticket_id   : ID tiket yang ingin dibeli
            client_clock: Lamport timestamp dari sisi client
        """

        # 1. Update Lamport Clock saat menerima request
        recv_ts = self._clock.receive(client_clock)

        # 2. Cek idempotency - apakah request ini sudah pernah diproses?
        idem_key = generate_idempotency_key(user_id, ticket_id)
        if self._idem_store.is_processed(idem_key):
            cached = self._idem_store.get_result(idem_key)
            self._log("DUPLICATE_REQUEST", {
                "user": user_id, "ticket": ticket_id,
                "note": "Idempotency: request sudah diproses sebelumnya"
            })
            return PurchaseResult(
                success=cached["result"]["success"],
                message=f"[DUPLICATE] {cached['result']['message']}",
                timestamp=recv_ts,
                is_duplicate=True
            )

        # 3. Simulasi network delay (50–200ms)
        time.sleep(random.uniform(0.05, 0.2))

        # 4. Critical Section — hanya satu thread masuk jika sync aktif
        if self.use_sync:
            self._mutex.acquire()   # LOCK 🔒

        try:
            result = self._process_purchase(user_id, ticket_id, recv_ts)
        finally:
            if self.use_sync:
                self._mutex.release()  # UNLOCK 🔓

        # 5. Simpan hasil ke idempotency store
        self._idem_store.save_result(idem_key, {
            "success": result.success,
            "message": result.message
        })

        return result

    def _process_purchase(self, user_id: str, ticket_id: str, recv_ts: int) -> PurchaseResult:
        """Critical section: cek ketersediaan dan proses transaksi."""

        ticket = self.tickets.get(ticket_id)

        if not ticket:
            ts = self._log("PURCHASE_FAILED", {
                "user": user_id, "ticket": ticket_id,
                "reason": "Tiket tidak ditemukan"
            })
            return PurchaseResult(False, "Tiket tidak ditemukan", timestamp=ts)

        if not ticket.is_available:
            ts = self._log("PURCHASE_FAILED", {
                "user": user_id, "ticket": ticket_id,
                "reason": f"Tiket sudah dibeli oleh {ticket.owner}"
            })
            return PurchaseResult(
                False,
                f"Tiket {ticket.seat} sudah habis (dimiliki oleh {ticket.owner})",
                timestamp=ts
            )

        # Tiket tersedia → proses pembelian
        ticket.is_available = False
        ticket.owner = user_id
        ts = self._log("PURCHASE_SUCCESS", {
            "user": user_id,
            "ticket": ticket_id,
            "seat": ticket.seat,
            "price": ticket.price
        })

        return PurchaseResult(
            True,
            f"Berhasil! {user_id} mendapatkan kursi {ticket.seat} (Rp {ticket.price:,})",
            ticket=ticket,
            timestamp=ts
        )

    # ── Status ─────────────────────────────────

    def get_available_tickets(self) -> list[Ticket]:
        with self._mutex if self.use_sync else threading.Lock():
            return [t for t in self.tickets.values() if t.is_available]

    def get_sold_tickets(self) -> list[Ticket]:
        return [t for t in self.tickets.values() if not t.is_available]

    def print_event_log(self, limit: int = 20):
        print(f"\n{'═'*60}")
        print(f"  EVENT LOG — {self.concert_name} (Lamport Clock Order)")
        print(f"{'═'*60}")
        logs = sorted(self.event_log, key=lambda x: x["lamport_ts"])
        for entry in logs[:limit]:
            icon = "✅" if entry["event"] == "PURCHASE_SUCCESS" else \
                   "🔁" if entry["event"] == "DUPLICATE_REQUEST" else "❌"
            user = entry.get("user", "-")
            seat = entry.get("seat", entry.get("ticket", "-"))
            print(f"  [{entry['lamport_ts']:>3}] {icon} {entry['event']:<20} | user={user:<12} seat={seat}")
        if len(self.event_log) > limit:
            print(f"  ... dan {len(self.event_log) - limit} event lainnya")
        print(f"{'═'*60}\n")
