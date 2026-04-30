import threading
from typing import Any, Dict, List, Optional, Tuple

import structlog


class PendingCargoRepo:

    def __init__(self, logger: structlog.stdlib.BoundLogger):
        self._logger = logger
        self._lock = threading.Lock()
        self._items: List[Dict[str, Any]] = []
        self._stamp_sec: Optional[float] = None

    def update(self, items: List[Dict[str, Any]], stamp_sec: Optional[float]) -> None:
        with self._lock:
            self._items = items
            self._stamp_sec = stamp_sec

    def snapshot(self) -> Tuple[List[Dict[str, Any]], Optional[float]]:
        with self._lock:
            return list(self._items), self._stamp_sec


def init_pending_cargo_repo(logger: structlog.stdlib.BoundLogger) -> PendingCargoRepo:
    return PendingCargoRepo(logger=logger)
