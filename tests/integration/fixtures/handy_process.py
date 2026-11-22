#!/usr/bin/env python3
"""Simulate Handy process commands for the apply tests."""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--process-error", action="store_true")
    parser.add_argument("--quit-fails", action="store_true")
    parser.add_argument("command", choices=("pgrep", "osascript", "open"))
    # Ignore the real commands' remaining arguments, such as pgrep's process name.
    args, _ = parser.parse_known_args()
    state = json.loads(args.state.read_text())
    if args.command == "pgrep":
        if args.process_error:
            return 2
        return 0 if state["running"] else 1
    if args.command == "osascript":
        state["quit"] += 1
        if not args.quit_fails:
            state["running"] = False
            # Simulate the settings Handy saves during a graceful shutdown.
            store = json.loads(args.settings.read_text())
            store["settings"]["flushed"] = True
            args.settings.write_text(json.dumps(store))
    if args.command == "open":
        state["running"] = True
        state["start"] += 1
    args.state.write_text(json.dumps(state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
