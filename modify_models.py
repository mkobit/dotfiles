import re

with open('src/python/claude_statusline/claude_statusline/models.py', 'r') as f:
    content = f.read()

# Add imports
content = content.replace(
    "from whenever import TimeDelta",
    "from whenever import Instant, TimeDelta"
)

# Replace SegmentGenerationResult
old_sgr = """class SegmentGenerationResult(BaseModel):
    segment: Segment
    generator: str = "internal"
    line: int = 1
    index: int = 0
    cache_duration: TimeDelta | None = None"""

new_sgr = """class SegmentGenerationResult(BaseModel):
    segment: Segment
    line: int = 1
    index: int = 0
    generator: str = "internal"
    cache_duration: TimeDelta | None = None

class CachedSegment(BaseModel):
    results: list[SegmentGenerationResult]
    expires_at: Instant"""

content = content.replace(old_sgr, new_sgr)

with open('src/python/claude_statusline/claude_statusline/models.py', 'w') as f:
    f.write(content)
