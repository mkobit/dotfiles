"""Small stdlib-only helpers used by the agent plugin bridge shell script."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path


def migrate_ownership(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    resources = payload.get("resources", [])
    lines = []
    for resource in resources:
        kind = resource["kind"]
        host = resource["host"]
        resource_id = resource["id"]
        if kind == "plugin":
            plugin, separator, marketplace = resource_id.rpartition("@")
            if not separator:
                raise ValueError(f"invalid legacy plugin identity: {resource_id}")
        elif kind == "marketplace":
            marketplace, plugin = resource_id, ""
        else:
            raise ValueError(f"invalid legacy resource kind: {kind}")
        lines.append(f"{kind}\t{host}\t{marketplace}\t{plugin}")
    return "\n".join(lines) + ("\n" if lines else "")


def has_identity(stream: str, field: str, expected: str) -> bool:
    value = json.loads(stream)
    records = value.get("marketplaces", []) if isinstance(value, Mapping) else value
    if not isinstance(records, list):
        raise TypeError("plugin host returned invalid JSON")
    return any(
        isinstance(item, Mapping) and item.get(field) == expected for item in records
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    migrate = commands.add_parser("migrate-ownership")
    migrate.add_argument("path", type=Path)
    identity = commands.add_parser("has-identity")
    identity.add_argument("--field", required=True)
    identity.add_argument("--expected", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate-ownership":
            sys.stdout.write(migrate_ownership(args.path))
            return 0
        return 0 if has_identity(sys.stdin.read(), args.field, args.expected) else 1
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"plugin-bridge: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
