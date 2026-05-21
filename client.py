"""
Client - Simulasi banyak user membeli tiket secara bersamaan
Week 10: Asynchronous Programming (menggunakan asyncio)
"""

import asyncio
import random
from typing import List

from lamport_clock import LamportClock
from ticket_server import PurchaseResult, TicketServer


class TicketClient:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.clock = LamportClock(user_id)
        self.results: List[PurchaseResult] = []

    async def buy_ticket_async(self, server: TicketServer, ticket_id: str, retries: int = 3) -> PurchaseResult:
        """[WEEK 10: ASYNC] Fungsi berjalan secara non-blocking."""
        for attempt in range(1, retries + 1):
            try:
                send_ts = self.clock.send()
                await asyncio.sleep(random.uniform(0.01, 0.1))
                result = server.purchase_ticket(self.user_id, ticket_id, client_clock=send_ts)
                self.clock.receive(result.timestamp)
                self.results.append(result)
                return result
            except ConnectionError:
                print(f"  [W9 - FAULT TOLERANCE] Koneksi putus, mencoba Retry ke-{attempt}...")
                await asyncio.sleep(0.5)

        return PurchaseResult(
            False,
            "Gagal terhubung ke server setelah maksimal retry.",
            timestamp=self.clock.get_time(),
        )

    async def double_submit_async(self, server: TicketServer, ticket_id: str) -> List[PurchaseResult]:
        """Simulasikan user melakukan double-submit pada tiket yang sama."""
        return await asyncio.gather(
            self.buy_ticket_async(server, ticket_id),
            self.buy_ticket_async(server, ticket_id),
        )
