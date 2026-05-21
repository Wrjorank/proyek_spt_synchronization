"""
Lamport Clock - Logical Clock for Distributed Event Ordering
Week 11: Synchronization - SPT Project
"""

import threading


class LamportClock:
    """Implementasi Lamport Clock untuk mengurutkan event kausal di sistem terdistribusi."""

    def __init__(self, process_id: str):
        self.process_id = process_id
        self.time = 0
        self._lock = threading.Lock()

    def tick(self) -> int:
        """Increment clock untuk internal event lokal."""
        with self._lock:
            self.time += 1
            return self.time

    def send(self) -> int:
        """Panggil sebelum mengirim pesan ke proses lain."""
        with self._lock:
            self.time += 1
            return self.time

    def receive(self, received_time: int) -> int:
        """Update clock saat menerima event dari proses lain."""
        with self._lock:
            self.time = max(self.time, received_time) + 1
            return self.time

    def get_time(self) -> int:
        with self._lock:
            return self.time

    def __repr__(self) -> str:
        return f"LamportClock(process={self.process_id}, time={self.time})"
