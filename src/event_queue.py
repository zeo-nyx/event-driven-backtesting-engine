"""Simple FIFO event queue built with collections.deque."""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from event import Event


class EventQueue:
    """Queue wrapper used by all modules to exchange events."""

    def __init__(self) -> None:
        self._queue: Deque[Event] = deque()

    def put(self, event: Event) -> None:
        """Append a new event to the queue."""
        self._queue.append(event)

    def get(self) -> Optional[Event]:
        """Pop the oldest event from the queue, if present."""
        if self._queue:
            return self._queue.popleft()
        return None

    def is_empty(self) -> bool:
        """Return True when no events are waiting."""
        return not self._queue
