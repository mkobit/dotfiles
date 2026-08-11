import asyncio
import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from whenever import Instant

from termstatus.layout import Segment, SegmentGenerationResult


@dataclass
class CachedSegment:
    results: list[SegmentGenerationResult]
    expires_at: Instant


logger = logging.getLogger(__name__)


class SegmentCache:
    def __init__(self, cache_file: Path) -> None:
        self.cache_file = cache_file
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.debug(f"Failed to create cache dir {self.cache_file.parent}: {e}")
        self._cache: dict[str, CachedSegment] = {}

    def load(self) -> None:
        if not self.cache_file.exists():
            return

        try:
            content = self.cache_file.read_text()
            if not content.strip():
                return

            raw_dict = json.loads(content)
            parsed: dict[str, CachedSegment] = {}
            for key, val in raw_dict.items():
                results = [
                    SegmentGenerationResult(
                        segment=Segment(text=item["segment"]["text"]),
                        line=item.get("line", 0),
                        index=item.get("index", 0),
                        column=item.get("column"),
                        generator=item.get("generator", "internal"),
                    )
                    for item in val.get("results", [])
                ]
                exp_str = val.get("expires_at")
                exp_instant = Instant.parse_iso(exp_str) if exp_str else Instant.now()
                parsed[key] = CachedSegment(results=results, expires_at=exp_instant)
            self._cache = parsed
        except (OSError, Exception) as e:
            logger.warning(f"Failed to load cache from {self.cache_file}: {e}")
            self._cache = {}

    async def _save(self) -> None:
        def do_save(cache_data: dict[str, CachedSegment]) -> None:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                serialized = {
                    key: {
                        "results": [
                            {
                                "segment": {"text": r.segment.text},
                                "line": r.line,
                                "index": r.index,
                                "column": r.column,
                                "generator": r.generator,
                                "cache_duration": str(r.cache_duration) if r.cache_duration is not None else None,
                            }
                            for r in cs.results
                        ],
                        "expires_at": str(cs.expires_at),
                    }
                    for key, cs in cache_data.items()
                }
                self.cache_file.write_text(json.dumps(serialized))
            except (OSError, Exception) as e:
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
