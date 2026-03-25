import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore


def transform_frontmatter(
    metadata: dict[str, Any], tool: str, scope: str
) -> dict[str, Any]:
    """Apply tool-specific and scope-specific transformations to the frontmatter."""
    transformed = metadata.copy()

    # Generic scope addition
    if "metadata" not in transformed or not isinstance(transformed["metadata"], dict):
        transformed["metadata"] = {}

    transformed["metadata"]["scope"] = scope
    transformed["metadata"]["target_tool"] = tool

    # Tool-specific logic (placeholder for future adaptations like extensions/slash commands)
    if tool == "claude":
        # Example: Claude might require a different capability name
        pass
    elif tool == "gemini":
        # Example: Gemini might require different formatting
        pass

    return transformed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform agentskills.io .md.json to tool-specific markdown."
    )
    parser.add_argument(
        "input_json", type=Path, help="Input .md.json file from process_skill.py"
    )
    parser.add_argument("output_md", type=Path, help="Output tool-specific .md file")
    parser.add_argument(
        "--tool",
        required=True,
        choices=["claude", "gemini", "cursor"],
        help="Target AI tool",
    )
    parser.add_argument(
        "--scope", required=True, choices=["user", "repo"], help="Scope of the skill"
    )

    args = parser.parse_args()

    try:
        with open(args.input_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        body = data.get("body", "")

        # Transform the metadata
        transformed_metadata = transform_frontmatter(metadata, args.tool, args.scope)

        # Generate the output markdown
        # PyYAML dumps with some defaults we want to override for frontmatter
        yaml_str = yaml.dump(
            transformed_metadata, default_flow_style=False, sort_keys=False
        )

        output_content = f"---\n{yaml_str}---\n\n{body}"

        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_md, "w", encoding="utf-8") as f:
            f.write(output_content)

        print(
            f"Successfully transformed {args.input_json} to {args.output_md} for {args.tool} ({args.scope} scope)"
        )

    except Exception as e:
        print(f"Error transforming {args.input_json}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
