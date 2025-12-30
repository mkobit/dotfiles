import argparse
import re
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Bundle Python scripts into a single file.")
    parser.add_argument("--main", required=True, help="Main entry point script.")
    parser.add_argument("--inline", action="append", help="Module to inline in format module_name:file_path")
    parser.add_argument("--output", required=True, help="Output file path.")
    parser.add_argument("--requirements", help="Path to requirements.in file to generate PEP 723 header.")
    return parser.parse_args()

def extract_header(content):
    """Extracts PEP 723 header (comment block starting with # /// script)."""
    lines = content.splitlines()
    header = []
    in_header = False
    rest = []

    for line in lines:
        if line.strip() == "# /// script":
            in_header = True
            header.append(line)
        elif line.strip() == "# ///" and in_header:
            header.append(line)
            in_header = False
        elif in_header:
            header.append(line)
        else:
            rest.append(line)

    return "\n".join(header) + "\n", "\n".join(rest)

def generate_header_from_requirements(req_path):
    """Generates PEP 723 header from requirements.in file."""
    if not req_path:
        return ""

    path = Path(req_path)
    if not path.exists():
        return ""

    deps = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            deps.append(line)

    header = ["# /// script", "# dependencies = ["]
    for dep in deps:
        header.append(f'#   "{dep}",')
    header.append("# ]")
    header.append("# ///")
    return "\n".join(header) + "\n"

def main():
    args = parse_args()

    main_path = Path(args.main)
    main_content = main_path.read_text(encoding="utf-8")

    # If requirements file is provided, generate header.
    # Otherwise check if main already has it.
    if args.requirements:
        header = generate_header_from_requirements(args.requirements)
        # Strip existing header from main if any
        _, main_body = extract_header(main_content)
    else:
        header, main_body = extract_header(main_content)

    inlined_content = []

    # Process inlines
    if args.inline:
        for inline_def in args.inline:
            mod_name, file_path = inline_def.split(":")
            path = Path(file_path)
            content = path.read_text(encoding="utf-8")

            # Simple stripping of the script header if present in libs
            _, body = extract_header(content)

            inlined_content.append(f"# --- Inlined {mod_name} ({file_path}) ---")
            inlined_content.append(body)
            inlined_content.append("")

            # Remove imports of this module from main_body
            main_body = re.sub(f'^from {mod_name} import .*$', '', main_body, flags=re.MULTILINE)
            main_body = re.sub(f'^import {mod_name}.*$', '', main_body, flags=re.MULTILINE)
            main_body = re.sub(f'^from .*\\.{mod_name} import .*$', '', main_body, flags=re.MULTILINE)

    # Remove the "sys.path.append" block and import try/except logic
    start_marker = "# --- START_IMPORTS ---"
    end_marker = "# --- END_IMPORTS ---"

    if start_marker in main_body and end_marker in main_body:
        pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
        main_body = re.sub(pattern, '', main_body, flags=re.DOTALL)

    final_content = header + "\n" + "\n".join(inlined_content) + "\n# --- Main ---\n" + main_body

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(final_content)

if __name__ == "__main__":
    main()
