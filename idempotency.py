"""
Idempotency - Safe Retry Mechanism
Week 11: Synchronization - SPT Project

Mencegah duplikasi transaksi meskipun request dikirim berkali-kali.
Contoh: User klik tombol beli tiket 2x karena jaringan lambat.
"""

import threading
import time
from typing import Any, Dict, Optional


class IdempotencyStore:
    """Penyimpanan hasil request berdasarkan idempotency key."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def is_processed(self, key: str) -> bool:
        """Periksa apakah key request sudah pernah diproses."""
        with self._lock:
            return key in self._store

    def get_result(self, key: str) -> Optional[Dict[str, Any]]:
        """Ambil hasil request yang sudah diproses."""
        with self._lock:
            return self._store.get(key)

    def save_result(self, key: str, result: Dict[str, Any]) -> None:
        """Simpan hasil request untuk idempotency."""
        with self._lock:
            self._store[key] = {
                "result": result,
                "timestamp": time.time(),
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


def generate_idempotency_key(user_id: str, ticket_id: str) -> str:
    """Generate idempotency key yang konsisten untuk user dan tiket."""
    return f"{user_id}:{ticket_id}"
