from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event, Lock
from time import sleep

import pytest

from weather_analysis.memory_cache import MemoryCache


def test_cache_returns_existing_value_before_expiration() -> None:
    calls = 0
    cache: MemoryCache[str, str] = MemoryCache()

    def factory() -> str:
        nonlocal calls
        calls += 1
        return "dữ liệu"

    assert cache.get_or_create("key", factory, timedelta(minutes=1)) == "dữ liệu"
    assert cache.get_or_create("key", factory, timedelta(minutes=1)) == "dữ liệu"
    assert calls == 1


def test_cache_refreshes_expired_value_with_fake_clock() -> None:
    now = 100.0
    cache: MemoryCache[str, int] = MemoryCache(lambda: now)
    calls = 0

    def factory() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert cache.get_or_create("key", factory, timedelta(seconds=30)) == 1
    now = 131.0
    assert cache.get_or_create("key", factory, timedelta(seconds=30)) == 2


def test_cache_does_not_store_factory_error() -> None:
    cache: MemoryCache[str, str] = MemoryCache()
    calls = 0

    def factory() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("lỗi thử nghiệm")
        return "thành công"

    with pytest.raises(RuntimeError, match="lỗi thử nghiệm"):
        cache.get_or_create("key", factory, timedelta(minutes=1))

    assert cache.get_or_create("key", factory, timedelta(minutes=1)) == "thành công"
    assert calls == 2


def test_concurrent_requests_for_same_key_share_one_fetch() -> None:
    cache: MemoryCache[str, str] = MemoryCache()
    barrier = Barrier(8)
    factory_started = Event()
    release_factory = Event()
    calls_lock = Lock()
    calls = 0

    def factory() -> str:
        nonlocal calls
        with calls_lock:
            calls += 1
        factory_started.set()
        assert release_factory.wait(timeout=5)
        return "dữ liệu"

    def get_value() -> str:
        barrier.wait(timeout=5)
        return cache.get_or_create("key", factory, timedelta(minutes=1))

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(get_value) for _ in range(8)]
        try:
            assert factory_started.wait(timeout=5)
            sleep(0.05)
        finally:
            release_factory.set()
        assert [future.result(timeout=5) for future in futures] == ["dữ liệu"] * 8

    assert calls == 1
