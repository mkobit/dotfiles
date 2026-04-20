from __future__ import annotations

from dataclasses import dataclass, field

from termtext.attribute import SGR, Attribute


@dataclass(frozen=True)
class Style:
    attributes: frozenset[Attribute] = field(default_factory=frozenset)

    def merge(self, other: Style) -> Style:
        """Merge two styles, with other taking precedence on type conflicts.

        SGR codes are additive (each value is distinct).
        FG, BG, and Link are replaced by the incoming value (last wins).
        """
        merged: dict[object, Attribute] = {
            (SGR, attr) if isinstance(attr, SGR) else type(attr): attr
            for attr in self.attributes
        }
        merged.update(
            {
                (SGR, attr) if isinstance(attr, SGR) else type(attr): attr
                for attr in other.attributes
            }
        )
        return Style(frozenset(merged.values()))
