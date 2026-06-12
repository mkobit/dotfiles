from pydantic import BaseModel
from whenever import TimeDelta


class Segment(BaseModel):
    text: str


class SegmentGenerationResult(BaseModel):
    segment: Segment
    line: int = 0
    index: int = 0
    column: int | None = None
    generator: str = "internal"
    cache_duration: TimeDelta | None = None
