"""
Main - Concert Ticket Booking System
======================================
Merangkum keseluruhan materi W9 - W13!
"""

import asyncio
import hashlib
import multiprocessing
import time
from typing import Dict, List

from client import TicketClient
from ticket_server import TicketServer


def generate_qr_signature(ticket_data: Dict[str, str]) -> Dict[str, str]:
    """Simulasi komputasi berat paralel: generate hash untuk QR Code tiket."""
    text = f"{ticket_data['user']}-{ticket_data['seat']}-NAWASENA"
    for _ in range(200000):
        hash_result = hashlib.sha256(text.encode()).hexdigest()
    return {"seat": ticket_data["seat"], "qr": hash_result[:15]}


async def run_simulation() -> None:
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     🎵 SISTEM PEMESANAN TIKET KONSER TERDISTRIBUSI "NAWA SENA" 🎵     ║
║     Integrasi penuh materi Week 9 sampai Week 13                  ║
╚════════════════════════════════════════════════════════════════════════╝
""")

    server = TicketServer("Nawa Sena", total_tickets=2, use_sync=True)
    target_ticket_race = "TKT-001"
    target_ticket_duplicate = "TKT-002"

    print(f"[W10 - ASYNC] Memulai request dari 4 user secara bersamaan untuk tiket {target_ticket_race}...\n")

    wahyu_client = TicketClient("Rian")
    clients = [
        TicketClient("Dina"),
        TicketClient("Citra"),
        TicketClient("Sakti"),
    ]

    tasks = [
        wahyu_client.buy_ticket_async(server, target_ticket_race),
        *[client.buy_ticket_async(server, target_ticket_race) for client in clients],
    ]

    results = await asyncio.gather(*tasks)

    print("\n" + "═" * 70)
    print("  HASIL PERLOMBAAN TIKET NAWA SENA")
    print("═" * 70)

    ordered_users: List[str] = ["Rian", "Dina", "Citra", "Sakti"]
    for user_label, result in zip(ordered_users, results):
        icon = "✅" if result.success and not result.is_duplicate else "🔁" if result.is_duplicate else "❌"
        print(f"  {icon} {user_label: <20} : {result.message}")

    print("\n[W11 - IDEMPOTENCY] Simulasi double-submit oleh Rian pada tiket TKT-002...")

    first_result = await wahyu_client.buy_ticket_async(server, target_ticket_duplicate)
    duplicate_result = await wahyu_client.buy_ticket_async(server, target_ticket_duplicate)

    print("\n" + "═" * 70)
    print("  HASIL DOUBLE SUBMIT RIAN")
    print("═" * 70)
    print(f"  {'✅' if first_result.success and not first_result.is_duplicate else '❌'} Rian pertama : {first_result.message}")
    print(f"  {'🔁' if duplicate_result.is_duplicate else '❌'} Rian kedua  : {duplicate_result.message}")

    await asyncio.sleep(1.5)

    sold_tickets = [{"user": ticket.owner or "unknown", "seat": ticket.seat} for ticket in server.get_sold_tickets()]

    print("\n" + "═" * 70)
    print("  [W13 - MULTIPROCESSING] Generate QR Code secara paralel di CPU")
    print("═" * 70)

    if sold_tickets:
        start_time = time.time()
        print("  Memulai komputasi berat untuk QR Code ...")
        with multiprocessing.Pool(processes=4) as pool:
            qr_results = pool.map(generate_qr_signature, sold_tickets)

        elapsed = time.time() - start_time
        for qr in qr_results:
            print(f"  🎫 Seat {qr['seat']} -> QR Code Signature: {qr['qr']}")

        print(f"  [W13 - MULTIPROCESSING] Generate QR Code secara paralel di CPU memakan waktu {elapsed:.4f} detik.")
    else:
        print("  Tidak ada tiket terjual, tidak ada QR Code yang di-generate.")


if __name__ == "__main__":
    asyncio.run(run_simulation())
