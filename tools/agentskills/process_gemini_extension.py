import json
import logging
import re
import sys
from pathlib import Path

import click

from tools.agentskills.models import SkillIR


@click.command()
@click.argument("extension_json", type=click.Path(exists=True, path_type=Path))
@click.argument("output_json", type=click.Path(path_type=Path))
def main(extension_json: Path, output_json: Path) -> None:
    """
    Parses a gemini-extension.json file (and its associated context file)
    and emits a SkillIR JSON that transform_skill can consume.
    """
    try:
        with open(extension_json, encoding="utf-8") as f:
            ext_data = json.load(f)

        name = ext_data.get("name", "unknown")
        # Ensure name conforms to agent_skill pattern
        # The skill model pattern is: ^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$
        clean_name = name.lower()
        clean_name = re.sub(r"[^a-z0-9-]", "-", clean_name)
        if not clean_name:
            clean_name = "unknown"
        clean_name = clean_name.strip("-")

        version = ext_data.get("version", "1.0.0")
        description = f"Gemini Extension: {name} v{version}"

        context_file_name = ext_data.get("contextFileName")
        body = ""

        if context_file_name:
            # context file path is relative to the extension.json file
            context_path = extension_json.parent / context_file_name
            if context_path.exists():
                with open(context_path, encoding="utf-8") as f:
                    body = f.read()
            else:
                body = f"<!-- Missing context file: {context_file_name} -->"

        ir = SkillIR(
            source_format="gemini-extension",
            name=clean_name,
            description=description,
            body=body,
        )

        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(ir.model_dump(mode="json", by_alias=True), f, indent=2)

        logging.debug(f"Successfully processed {extension_json} to {output_json}")
    except Exception as e:
        click.echo(f"Error processing {extension_json}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
