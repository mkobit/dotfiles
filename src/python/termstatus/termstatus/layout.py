from dataclasses import dataclass

from whenever import TimeDelta


@dataclass
class Segment:
    text: str


@dataclass
class SegmentGenerationResult:
    segment: Segment
    line: int = 0
    index: int = 0
    column: int | None = None
    generator: str = "internal"
    cache_duration: TimeDelta | None = None
