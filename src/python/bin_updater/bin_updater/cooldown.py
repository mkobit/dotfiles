from datetime import UTC, datetime, timedelta


def parse_cooldown_to_seconds(raw: str | int | None, default_days: int = 7) -> int:
    """Parse cooldown specification to seconds."""
    if raw is None:
        return default_days * 86400
    if isinstance(raw, int):
        return raw * 86400
    if isinstance(raw, str):
        cleaned = raw.strip()
        if not cleaned:
            return default_days * 86400
        if cleaned.endswith(("d", "D")) and cleaned[:-1].isdigit():
            return int(cleaned[:-1]) * 86400
        if cleaned.isdigit():
            return int(cleaned) * 86400
        raise ValueError(f"Invalid cooldown format: '{raw}'")
    raise TypeError(f"Unsupported cooldown type: {type(raw)}")


def is_release_mature(published_at_iso: str, cooldown_seconds: int, now: datetime | None = None) -> bool:
    """Check if release published timestamp has cleared cooldown window."""
    published_dt = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
    pub_aware = published_dt if published_dt.tzinfo is not None else published_dt.replace(tzinfo=UTC)
    current_dt = now or datetime.now(UTC)
    now_aware = current_dt if current_dt.tzinfo is not None else current_dt.replace(tzinfo=UTC)
    cutoff = now_aware - timedelta(seconds=cooldown_seconds)
    return pub_aware <= cutoff
