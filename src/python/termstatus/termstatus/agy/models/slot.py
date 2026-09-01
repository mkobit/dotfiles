from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Slot:
    line: int
    index: int
    minimum_width: int
    text: str
