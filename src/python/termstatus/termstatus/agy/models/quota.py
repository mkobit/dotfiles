from dataclasses import dataclass

from whenever import TimeDelta


@dataclass(frozen=True, slots=True)
class Quota:
    remaining: int
    reset_in: TimeDelta | None
