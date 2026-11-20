"""Format release metadata for binary update pull requests."""

from datetime import UTC, datetime


def release_date(published_at: str) -> datetime:
    date = datetime.fromisoformat(published_at)
    return date.replace(tzinfo=UTC) if date.tzinfo is None else date.astimezone(UTC)


def update_table(old: str, new: str, published_at: str, cooldown_seconds: int) -> str:
    date = release_date(published_at).date().isoformat()
    return (
        "| Current version | Target version | Target release date (UTC) | Cooldown |\n"
        "| --- | --- | --- | --- |\n"
        f"| `{old}` | `{new}` | {date} | `{cooldown_seconds // 86400}d` |"
    )
