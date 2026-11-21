"""Print a Markdown table of the slowest integration tests."""

import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path


def main(report: Path, runner: str) -> None:
    if not report.is_file():
        return

    durations = []
    for test in ET.parse(report).iter("testcase"):
        if test.find("skipped") is not None or "time" not in test.attrib:
            continue
        name = "::".join(filter(None, (test.get("classname"), test.attrib["name"])))
        durations.append((float(test.attrib["time"]), name))

    if not durations:
        return

    print(f"### Slowest integration tests ({runner})\n")
    print("| Test | Duration (s) |")
    print("| --- | ---: |")
    for duration, name in sorted(durations, reverse=True)[:20]:
        label = escape(" ".join(name.splitlines())).replace("|", "&#124;")
        print(f"| <code>{label}</code> | {duration:.3f} |")


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
