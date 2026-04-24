import logging
from pathlib import Path

import pytest
from whenever import Instant, hours

from claude_statusline.cache import SegmentCache
from claude_statusline.models import Segment, SegmentGenerationResult


@pytest.fixture
def cache_file(tmp_path: Path) -> Path:
    return tmp_path / "cache.json"


@pytest.fixture
def cache(cache_file: Path) -> SegmentCache:
    return SegmentCache(cache_file)


@pytest.mark.asyncio
async def test_cache_miss_when_empty(cache: SegmentCache) -> None:
    """Goals: Missing keys return None without error."""
    assert await cache.get("nonexistent") is None


@pytest.mark.asyncio
async def test_cache_set_and_get(cache: SegmentCache, cache_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Goals: Cache persists and retrieves data in bi-directional flows."""
    results = [SegmentGenerationResult(line=0, index=0, generator="test", segment=Segment(text="hello"))]

    fixed_now = Instant.from_utc(2024, 1, 1, 12, 0, 0)
    expires = fixed_now + hours(1)

    await cache.set("key1", results, expires)

    class MockInstant:
        @classmethod
        def now(cls):
            return fixed_now

    monkeypatch.setattr("claude_statusline.cache.Instant", MockInstant)

    cached = await cache.get("key1")
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].segment.text == "hello"


@pytest.mark.asyncio
async def test_cache_expires(cache: SegmentCache, monkeypatch: pytest.MonkeyPatch) -> None:
    """Goals: Ensure expired cache state subtracts correctly."""
    results = [SegmentGenerationResult(line=0, index=0, generator="test", segment=Segment(text="hello"))]

    fixed_now = Instant.from_utc(2024, 1, 1, 12, 0, 0)
    expires = fixed_now - hours(1)

    await cache.set("key1", results, expires)

    class MockInstant:
        @classmethod
        def now(cls):
            return fixed_now

    monkeypatch.setattr("claude_statusline.cache.Instant", MockInstant)

    assert await cache.get("key1") is None
    assert "key1" not in cache._cache


@pytest.mark.asyncio
async def test_cache_load_valid(cache_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Goals: Verify data loads from disk reliably."""
    results = [SegmentGenerationResult(line=0, index=0, generator="test", segment=Segment(text="hello"))]

    fixed_now = Instant.from_utc(2024, 1, 1, 12, 0, 0)
    expires = fixed_now + hours(1)

    initial_cache = SegmentCache(cache_file)
    await initial_cache.set("key1", results, expires)

    new_cache = SegmentCache(cache_file)
    new_cache.load()

    class MockInstant:
        @classmethod
        def now(cls):
            return fixed_now

    monkeypatch.setattr("claude_statusline.cache.Instant", MockInstant)

    cached = await new_cache.get("key1")
    assert cached is not None
    assert cached[0].segment.text == "hello"


def test_cache_load_invalid(cache_file: Path) -> None:
    """Goals: Invalid cache data clears state automatically."""
    cache_file.write_text('{"bad": "json"')

    cache = SegmentCache(cache_file)
    cache.load()

    assert cache._cache == {}


def test_cache_load_empty(cache_file: Path) -> None:
    """Goals: Empty cache files handle safely without fault."""
    cache_file.write_text("   \n")

    cache = SegmentCache(cache_file)
    cache.load()

    assert cache._cache == {}


@pytest.mark.asyncio
async def test_cache_save_io_error(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Goals: Gracefully degrade if the file system prevents cache saving."""
    readonly_dir = tmp_path / "dir_cannot_be_file"
    readonly_dir.mkdir()

    bad_cache = SegmentCache(readonly_dir)
    results = [SegmentGenerationResult(line=0, index=0, generator="test", segment=Segment(text="hello"))]

    fixed_now = Instant.from_utc(2024, 1, 1, 12, 0, 0)
    with caplog.at_level(logging.WARNING):
        await bad_cache.set("key1", results, fixed_now + hours(1))

    assert "Failed to save cache to" in caplog.text


def test_cache_load_io_error(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Goals: Gracefully reset if the cache file is unreadable."""
    readonly_dir = tmp_path / "dir_cannot_be_file"
    readonly_dir.mkdir()

    bad_cache = SegmentCache(readonly_dir)

    with caplog.at_level(logging.WARNING):
        bad_cache.load()

    assert bad_cache._cache == {}
    assert "Failed to load cache from" in caplog.text
