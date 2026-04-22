import logging
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
from whenever import Instant

from claude_statusline.models import CachedSegment, SegmentGenerationResult

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

    def _save(self) -> None:
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(CACHE_ADAPTER.dump_json(self._cache).decode("utf-8"))
        except (OSError, ValidationError) as e:
            logger.warning(f"Failed to save cache to {self.cache_file}: {e}")

    def get(self, key: str) -> list[SegmentGenerationResult] | None:
        if key in self._cache:
            cached = self._cache[key]
            if cached.expires_at > Instant.now():
                return cached.results
            self._cache = {k: v for k, v in self._cache.items() if k != key}
            self._save()
        return None

    def set(self, key: str, results: list[SegmentGenerationResult], expires_at: Instant) -> None:
        self._cache[key] = CachedSegment(results=results, expires_at=expires_at)
        self._save()
