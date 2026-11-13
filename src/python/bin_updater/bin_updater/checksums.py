from collections.abc import Mapping, Sequence
from typing import Any

EXCLUDED_SIGNATURE_EXTENSIONS = (".sig", ".asc", ".pem")


def parse_checksum_manifest(content: str) -> Mapping[str, str]:
    """Parse SHA256SUMS or checksums manifest text into filename-to-hash mapping."""
    lines = (line.strip() for line in content.splitlines())
    parts_list = (line.split(None, 1) for line in lines if line and not line.startswith("#"))
    return {parts[1].strip().lstrip("*"): parts[0].strip() for parts in parts_list if len(parts) == 2}


def find_checksum_manifest_asset(assets: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Find release asset matching checksum manifest naming conventions."""

    def _is_manifest_name(name: str) -> bool:
        if not name or any(name.endswith(ext) for ext in EXCLUDED_SIGNATURE_EXTENSIONS):
            return False
        lower = name.lower()
        return "_SHA256SUMS" in name or "SHA256SUMS" in name or "checksums.txt" in lower

    return next((a for a in assets if _is_manifest_name(str(a.get("name", "")))), None)
