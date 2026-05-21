"""
Ticket Server - Inti dari sistem pemesanan tiket konser
Week 9  : Fault Tolerance (Replikasi Data Primary-Backup)
Week 11 : Synchronization (Mutex, Lamport Clock, Idempotency)
Week 12 : Concurrency (Thread Pool untuk Notifikasi)
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from idempotency import IdempotencyStore, generate_idempotency_key
from lamport_clock import LamportClock


class Ticket:
    def __init__(self, ticket_id: str, seat: str, price: int) -> None:
        self.ticket_id = ticket_id
        self.seat = seat
        self.price = price
        self.is_available = True
        self.owner: Optional[str] = None

    def __repr__(self) -> str:
        return f"Ticket({self.ticket_id}, seat={self.seat}, owner={self.owner})"


class PurchaseResult:
    def __init__(
        self,
        success: bool,
        message: str,
        ticket: Optional[Ticket] = None,
        timestamp: int = 0,
        is_duplicate: bool = False,
    ) -> None:
        self.success = success
        self.message = message
        self.ticket = ticket
        self.timestamp = timestamp
        self.is_duplicate = is_duplicate


class TicketServer:
    def __init__(self, concert_name: str, total_tickets: int, use_sync: bool = True) -> None:
        self.concert_name = concert_name
        self.use_sync = use_sync

        # [WEEK 9: REPLICATION] Database Utama & Backup
        self.db_primary: Dict[str, Ticket] = {}
        self.db_backup: Dict[str, Ticket] = {}
        for i in range(1, total_tickets + 1):
            ticket_id = f"TKT-{i:03d}"
            ticket = Ticket(ticket_id, f"VIP-{i}", 1500000)
            self.db_primary[ticket_id] = ticket
            self.db_backup[ticket_id] = Ticket(ticket_id, ticket.seat, ticket.price)

        self._mutex = threading.Lock()
        self._idem_store = IdempotencyStore()
        self.server_clock = LamportClock("Server-1")
        self.event_log: List[Dict[str, object]] = []

        # [WEEK 12: CONCURRENCY] Thread Pool untuk tugas background
        self.email_executor = ThreadPoolExecutor(max_workers=3)

    def _send_email_notification(self, user_id: str, seat: str) -> None:
        """Tugas background yang tidak memblokir server utama."""
        time.sleep(1)
        print(f"  [W12 - CONCURRENCY] E-Ticket dikirim ke email via background thread... user={user_id}, seat={seat}")

    def _replicate_to_backup(self, ticket_id: str, owner: str) -> None:
        backup_ticket = self.db_backup.get(ticket_id)
        if backup_ticket:
            backup_ticket.is_available = False
            backup_ticket.owner = owner
            print("  [W9 - REPLICATION] Data disalin ke Backup DB.")

    def purchase_ticket(self, user_id: str, ticket_id: str, client_clock: int) -> PurchaseResult:
        # [WEEK 9: FAULT TOLERANCE] Simulasi transient fault dengan probabilitas 40-50%.
        if random.random() < 0.45:
            raise ConnectionError("Timeout: jaringan terputus ke server!")

        current_ts = self.server_clock.receive(client_clock)
        idem_key = generate_idempotency_key(user_id, ticket_id)

        # [WEEK 11: IDEMPOTENCY] Cek duplikat sebelum memproses transaksi.
        if self._idem_store.is_processed(idem_key):
            cached = self._idem_store.get_result(idem_key)
            ticket = None
            if cached is not None:
                ticket = cached.get("ticket")

            print("  [W11 - IDEMPOTENCY] Duplikat request terdeteksi, saldo aman tidak terpotong dua kali.")
            self.event_log.append(
                {
                    "lamport_ts": current_ts,
                    "event": "DUPLICATE_REQUEST",
                    "user": user_id,
                    "ticket_id": ticket_id,
                }
            )
            return PurchaseResult(
                True,
                "Duplikat request terdeteksi - Safe Retry aktif.",
                ticket=ticket,
                timestamp=current_ts,
                is_duplicate=True,
            )

        if self.use_sync:
            self._mutex.acquire()

        try:
            ticket = self.db_primary.get(ticket_id)
            if ticket is None or not ticket.is_available:
                self.event_log.append(
                    {
                        "lamport_ts": current_ts,
                        "event": "PURCHASE_FAILED",
                        "user": user_id,
                        "ticket_id": ticket_id,
                    }
                )
                return PurchaseResult(False, "Tiket sudah habis atau tidak ditemukan.", timestamp=current_ts)

            ticket.is_available = False
            ticket.owner = user_id
            self._replicate_to_backup(ticket_id, user_id)
            self._idem_store.save_result(idem_key, {"ticket": ticket})
            self.event_log.append(
                {
                    "lamport_ts": current_ts,
                    "event": "PURCHASE_SUCCESS",
                    "user": user_id,
                    "ticket_id": ticket_id,
                }
            )

            self.email_executor.submit(self._send_email_notification, user_id, ticket.seat)
            return PurchaseResult(True, f"Berhasil memesan tiket {ticket.seat}.", ticket=ticket, timestamp=current_ts)
        finally:
            if self.use_sync:
                self._mutex.release()

    def get_sold_tickets(self) -> List[Ticket]:
        return [ticket for ticket in self.db_primary.values() if not ticket.is_available]

    def get_event_log(self) -> List[Dict[str, object]]:
        return list(self.event_log)
