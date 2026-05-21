"""
Lamport Clock - Logical Clock for Distributed Event Ordering
Week 11: Synchronization - SPT Project
"""

import threading


class LamportClock:
    """
    Implementasi Lamport Clock untuk mengurutkan event
    di sistem terdistribusi tanpa bergantung pada physical time.
    
    Aturan:
    1. Setiap proses punya counter sendiri
    2. Setiap event: increment counter
    3. Saat kirim pesan: sertakan timestamp
    4. Saat terima pesan: clock = max(local, received) + 1
    """

    def __init__(self, process_id: str):
        self.process_id = process_id
        self.time = 0
        self._lock = threading.Lock()

    def tick(self) -> int:
        """Increment clock untuk internal event."""
        with self._lock:
            self.time += 1
            return self.time

    def send(self) -> int:
        """Increment clock sebelum mengirim pesan."""
        with self._lock:
            self.time += 1
            return self.time

    def receive(self, received_time: int) -> int:
        """
        Update clock saat menerima pesan.
        clock = max(local_clock, received_clock) + 1
        """
        with self._lock:
            self.time = max(self.time, received_time) + 1
            return self.time

    def get_time(self) -> int:
        with self._lock:
            return self.time

    def __repr__(self):
        return f"LampartClock(process={self.process_id}, time={self.time})"
