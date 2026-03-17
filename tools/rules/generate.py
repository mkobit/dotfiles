"""Generate tool-specific rule files from canonical sources in .rules/.

Reads markdown files with YAML frontmatter and produces outputs for:
  - Claude Code:  .claude/rules/{name}.md   (YAML frontmatter with paths)
  - Cursor:       .cursor/rules/{name}.mdc  (YAML frontmatter with globs)
  - Gemini CLI:   .gemini/memories/{name}.md (plain markdown)
  - Codex CLI:    .codex/memories/{name}.md  (plain markdown)
  - CLAUDE.md:    root file (body of root-flagged rules)
  - GEMINI.md:    root file (TOON index + body of root-flagged rules)

Usage: bazel run //tools/rules:generate
"""

import os
import sys
from pathlib import Path

import frontmatter


def to_claude(post: frontmatter.Post) -> str:
    """Format for Claude Code (.claude/rules/*.md)."""
    out = frontmatter.Post(post.content, paths=post.get("paths", ["**/*"]))
    return str(frontmatter.dumps(out)) + "\n"


def to_cursor(post: frontmatter.Post) -> str:
    """Format for Cursor (.cursor/rules/*.mdc)."""
    paths: list[str] = post.get("paths", ["**/*"])
    always = paths == ["**/*"]
    globs = "*" if always else ",".join(paths)
    out = frontmatter.Post(
        post.content,
        alwaysApply=always,
        description=post.get("description", ""),
        globs=globs,
    )
    return str(frontmatter.dumps(out)) + "\n"


def to_plain(post: frontmatter.Post) -> str:
    """Format for Gemini/Codex (plain markdown, no frontmatter)."""
    return str(post.content).lstrip("\n") + "\n"


def generate_gemini_md(
    rules: list[tuple[str, frontmatter.Post]],
) -> str:
    """Generate GEMINI.md root file with TOON index and preferences."""
    indexed = []
    root_bodies = []
    for name, post in rules:
        if post.get("root"):
            root_bodies.append(post.content.strip())
        else:
            indexed.append((name, post))

    lines = [
        "Please also reference the following rules as needed."
        " The list below is provided in TOON format,"
        " and `@` stands for the project root directory.",
        "",
        f"rules[{len(indexed)}]:",
    ]
    for name, post in indexed:
        desc = post.get("description", "")
        paths: list[str] = post.get("paths", ["**/*"])
        apply_to = ",".join(paths)
        lines.append(f"  - path: @.gemini/memories/{name}.md")
        lines.append(f"    description: {desc}")
        lines.append(f"    applyTo[{len(paths)}]: {apply_to}")

    lines.append("")
    lines.append("# Additional Conventions Beyond the Built-in Functions")
    lines.append("")
    lines.append(
        "As this project's AI coding tool, you must follow"
        " the additional conventions below,"
        " in addition to the built-in functions."
    )

    for body in root_bodies:
        lines.append("")
        lines.append(body)

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    workspace = Path(os.environ.get("BUILD_WORKSPACE_DIRECTORY", "."))
    rules_dir = workspace / ".rules"

    if not rules_dir.is_dir():
        print(f"No .rules/ directory found in {workspace}", file=sys.stderr)
        sys.exit(1)

    rules: list[tuple[str, frontmatter.Post]] = []
    for rule_file in sorted(rules_dir.glob("*.md")):
        name = rule_file.stem
        post = frontmatter.load(rule_file)
        rules.append((name, post))

    if not rules:
        print("No rule files found in .rules/", file=sys.stderr)
        sys.exit(1)

    changed = 0

    for name, post in rules:
        is_root = post.get("root", False)

        if is_root:
            changed += write_if_changed(workspace / "CLAUDE.md", to_plain(post))
        else:
            changed += write_if_changed(
                workspace / ".claude" / "rules" / f"{name}.md",
                to_claude(post),
            )

        changed += write_if_changed(
            workspace / ".cursor" / "rules" / f"{name}.mdc",
            to_cursor(post),
        )

        if not is_root:
            changed += write_if_changed(
                workspace / ".gemini" / "memories" / f"{name}.md",
                to_plain(post),
            )
            changed += write_if_changed(
                workspace / ".codex" / "memories" / f"{name}.md",
                to_plain(post),
            )

    changed += write_if_changed(workspace / "GEMINI.md", generate_gemini_md(rules))

    print(f"Generated rules for 4 tools. {changed} file(s) updated.")


def write_if_changed(path: Path, content: str) -> int:
    """Write content to path only if it differs. Returns 1 if written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text() == content:
        return 0
    path.write_text(content)
    return 1


if __name__ == "__main__":
    main()
