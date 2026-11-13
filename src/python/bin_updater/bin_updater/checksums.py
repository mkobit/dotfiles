import re
from collections.abc import Mapping, Sequence
from typing import Any

EXCLUDED_SIGNATURE_EXTENSIONS = (".sig", ".asc", ".pem", ".minisig", ".sigstore", ".sbom", ".json")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def parse_checksum_manifest(content: str) -> Mapping[str, str]:
    """Parse SHA256SUMS or checksums manifest text into filename-to-hash mapping."""
    lines = (line.strip() for line in content.splitlines())
    parts_list = (line.split(None, 1) for line in lines if line and not line.startswith("#"))
    result: dict[str, str] = {}
    for parts in parts_list:
        if len(parts) != 2:
            continue
        digest = parts[0].strip()
        filename = parts[1].strip().lstrip("*").removeprefix("./")
        if filename and _SHA256_RE.match(digest):
            result[filename] = digest
    return result


def find_checksum_manifest_asset(assets: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Find release asset matching checksum manifest naming conventions."""

    def _is_manifest_name(name: str) -> bool:
        if not name:
            return False
        lower = name.lower()
        if any(lower.endswith(ext) for ext in EXCLUDED_SIGNATURE_EXTENSIONS):
            return False
        return "sha256sum" in lower or "checksums" in lower

    return next((a for a in assets if _is_manifest_name(str(a.get("name", "")))), None)
