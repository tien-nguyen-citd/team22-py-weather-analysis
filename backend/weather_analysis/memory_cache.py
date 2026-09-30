import time
from collections.abc import Callable, Hashable
from concurrent.futures import Future
from datetime import timedelta
from threading import Lock


class MemoryCache[K: Hashable, V]:
    """Cache trong bộ nhớ với thời hạn hết hạn tuyệt đối."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._entries: dict[K, tuple[float, V]] = {}
        self._inflight: dict[K, Future[V]] = {}
        self._lock = Lock()

    def get_or_create(
        self,
        key: K,
        factory: Callable[[], V],
        ttl: timedelta,
    ) -> V:
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                expires_at, value = entry
                if expires_at > self._clock():
                    return value
                del self._entries[key]
            pending = self._inflight.get(key)
            if pending is None:
                pending = Future[V]()
                self._inflight[key] = pending
                should_create = True
            else:
                should_create = False

        if not should_create:
            return pending.result()

        try:
            value = factory()
        except BaseException as error:
            with self._lock:
                pending.set_exception(error)
                del self._inflight[key]
            raise
        else:
            with self._lock:
                expires_at = self._clock() + ttl.total_seconds()
                self._entries[key] = (expires_at, value)
                pending.set_result(value)
                del self._inflight[key]
            return value
