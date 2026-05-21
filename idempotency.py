"""
Idempotency - Safe Retry Mechanism
Week 11: Synchronization - SPT Project

Mencegah duplikasi transaksi meskipun request dikirim berkali-kali.
Contoh: User klik tombol beli tiket 2x karena jaringan lambat.
"""

import threading
import uuid
import time
from typing import Optional


class IdempotencyStore:
    """
    Menyimpan hasil request berdasarkan idempotency_key.
    Jika key yang sama dikirim ulang, kembalikan hasil yang sudah ada
    tanpa memproses ulang.
    """

    def __init__(self):
        self._store: dict = {}       # key -> result
        self._lock = threading.Lock()

    def is_processed(self, key: str) -> bool:
        """Cek apakah request dengan key ini sudah pernah diproses."""
        with self._lock:
            return key in self._store

    def get_result(self, key: str) -> Optional[dict]:
        """Ambil hasil dari request yang sudah diproses."""
        with self._lock:
            return self._store.get(key)

    def save_result(self, key: str, result: dict):
        """Simpan hasil request."""
        with self._lock:
            self._store[key] = {
                "result": result,
                "timestamp": time.time()
            }

    def clear(self):
        with self._lock:
            self._store.clear()


def generate_idempotency_key(user_id: str, ticket_id: str) -> str:
    """
    Generate unique key berdasarkan user + tiket.
    Jika user yang sama mencoba beli tiket yang sama → key identik.
    """
    return f"{user_id}:{ticket_id}"
