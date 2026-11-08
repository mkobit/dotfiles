import unicodedata


def normalized_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = "".join(char for char in value if not unicodedata.category(char).startswith("C")).strip()
    return text or None
