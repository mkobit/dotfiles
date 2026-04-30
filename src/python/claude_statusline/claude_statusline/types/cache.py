from pydantic import BaseModel
from whenever import Instant

from claude_statusline.types.layout import SegmentGenerationResult


class CachedSegment(BaseModel):
    results: list[SegmentGenerationResult]
    expires_at: Instant
