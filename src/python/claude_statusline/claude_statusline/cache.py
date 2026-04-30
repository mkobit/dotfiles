import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
from whenever import Instant

from claude_statusline.types.cache import CachedSegment
from claude_statusline.types.layout import SegmentGenerationResult

logger = logging.getLogger(__name__)

CACHE_ADAPTER = TypeAdapter(dict[str, CachedSegment])


class SegmentCache:
    def __init__(self, cache_file: Path) -> None:
        self.cache_file = cache_file
        self._cache: dict[str, CachedSegment] = {}

    def load(self) -> None:
        if not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text()
            if not content.strip():
                return

            self._cache = CACHE_ADAPTER.validate_json(content)
        except (OSError, ValidationError) as e:
            logger.warning(f"Failed to load cache from {self.cache_file}: {e}")
            self._cache = {}

    async def _save(self) -> None:
        def do_save(cache_data: dict[str, CachedSegment]) -> None:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                self.cache_file.write_text(CACHE_ADAPTER.dump_json(cache_data).decode("utf-8"))
            except (OSError, ValidationError) as e:
                logger.warning(f"Failed to save cache to {self.cache_file}: {e}")

        await asyncio.to_thread(do_save, dict(self._cache))

    async def get(self, key: str) -> list[SegmentGenerationResult] | None:
        if key in self._cache:
            cached = self._cache[key]
            if cached.expires_at > Instant.now():
                return cached.results
            self._cache = {k: v for k, v in self._cache.items() if k != key}
            await self._save()
        return None

    async def set_many(self, updates: Sequence[tuple[str, list[SegmentGenerationResult], Instant]]) -> None:
        for key, results, expires_at in updates:
            self._cache[key] = CachedSegment(results=results, expires_at=expires_at)
        await self._save()

    async def set(self, key: str, results: list[SegmentGenerationResult], expires_at: Instant) -> None:
        await self.set_many([(key, results, expires_at)])
