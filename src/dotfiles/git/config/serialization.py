from .section import Section
from typing import Iterable


def dumps(sections: Section | Iterable[Section]) -> str:
    if isinstance(sections, Section):
        sections = [sections]

    return "\n".join(__to_config_str(s) for s in sections)


def __to_config_str(section: Section) -> str:
    file_options = section.file_options()
    if not file_options:
        return ""

    file_options = "\n    ".join(
        f"{key} = {value}" for key, value in section.__dict__.items()
    )
    return f"[{section.name}]\n    {file_options}"
