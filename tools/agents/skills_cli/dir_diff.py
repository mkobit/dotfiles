"""Directory-level skill drift test for Bazel py_test targets.

Takes two SKILL.md paths as positional args, derives parent directories,
and compares them recursively. Exits non-zero if directories differ.

This is a standalone script (no Click) because it's invoked by Bazel
py_test with positional arguments.
"""

import sys
from pathlib import Path

from tools.agents.skills_cli.core import _dirs_match


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <source-SKILL.md> <target-SKILL.md>")
        sys.exit(1)

    source_dir = Path(sys.argv[1]).parent
    target_dir = Path(sys.argv[2]).parent

    if not source_dir.is_dir():
        print(f"FAIL: Source directory not found: {source_dir}")
        sys.exit(1)

    if not target_dir.is_dir():
        print(f"FAIL: Target directory not found: {target_dir}")
        print("Run: bazel run //tools/agents:sync")
        sys.exit(1)

    if not _dirs_match(source_dir, target_dir):
        print()
        print("Skill directories differ.")
        print(f"Source: {source_dir}")
        print(f"Target: {target_dir}")
        print("Run: bazel run //tools/agents:sync")
        sys.exit(1)


if __name__ == "__main__":
    main()
