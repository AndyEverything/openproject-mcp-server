"""Tests for src.utils.cache.TTLCache."""

import asyncio

import pytest

from src.utils.cache import DEFAULT_CACHE_TTL_SECONDS, TTLCache, ttl_from_env


class Counter:
    def __init__(self, value="v", delay=0.0):
        self.calls = 0
        self.value = value
        self.delay = delay

    async def __call__(self):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        return {"value": self.value, "items": [1, 2]}


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


async def test_two_reads_within_ttl_call_factory_once():
    cache = TTLCache(ttl=60, clock=FakeClock())
    factory = Counter()

    assert await cache.get_or_set("k", factory) == await cache.get_or_set("k", factory)
    assert factory.calls == 1


async def test_concurrent_reads_call_factory_once():
    cache = TTLCache(ttl=60)
    factory = Counter(delay=0.01)

    await asyncio.gather(*(cache.get_or_set("k", factory) for _ in range(5)))

    assert factory.calls == 1


async def test_expired_entry_is_refetched():
    clock = FakeClock()
    cache = TTLCache(ttl=60, clock=clock)
    factory = Counter()

    await cache.get_or_set("k", factory)
    clock.now = 59.9
    await cache.get_or_set("k", factory)
    clock.now = 60.0
    await cache.get_or_set("k", factory)

    assert factory.calls == 2


async def test_ttl_zero_disables_cache():
    cache = TTLCache(ttl=0)
    factory = Counter()

    await cache.get_or_set("k", factory)
    await cache.get_or_set("k", factory)

    assert factory.calls == 2


async def test_clear_and_invalidate():
    cache = TTLCache(ttl=60, clock=FakeClock())
    factory = Counter()

    await cache.get_or_set("k", factory)
    cache.invalidate("k")
    await cache.get_or_set("k", factory)
    cache.clear()
    await cache.get_or_set("k", factory)

    assert factory.calls == 3


async def test_factory_error_is_not_cached():
    cache = TTLCache(ttl=60, clock=FakeClock())
    calls = 0

    async def failing():
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cache.get_or_set("k", failing)
    assert calls == 2


async def test_returned_values_are_independent_copies():
    cache = TTLCache(ttl=60, clock=FakeClock())

    first = await cache.get_or_set("k", Counter())
    first["items"].append(3)

    assert (await cache.get_or_set("k", Counter()))["items"] == [1, 2]


@pytest.mark.parametrize(
    "env, expected",
    [
        ({}, DEFAULT_CACHE_TTL_SECONDS),
        ({"OPENPROJECT_CACHE_TTL": ""}, DEFAULT_CACHE_TTL_SECONDS),
        ({"OPENPROJECT_CACHE_TTL": "0"}, 0),
        ({"OPENPROJECT_CACHE_TTL": "30"}, 30),
        ({"OPENPROJECT_CACHE_TTL": "-5"}, 0),
        ({"OPENPROJECT_CACHE_TTL": "abc"}, DEFAULT_CACHE_TTL_SECONDS),
    ],
)
def test_ttl_from_env(env, expected):
    assert ttl_from_env(env) == expected


def test_default_ttl_comes_from_env(monkeypatch):
    monkeypatch.setenv("OPENPROJECT_CACHE_TTL", "0")

    assert TTLCache().enabled is False
