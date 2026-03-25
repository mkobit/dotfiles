import sys
import json
import argparse
import frontmatter


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extracts YAML frontmatter from a Markdown file to JSON."
    )
    parser.add_argument("input_md", help="Path to the input Markdown file.")
    parser.add_argument("output_json", help="Path to the output JSON file.")

    args = parser.parse_args()

    try:
        with open(args.input_md, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        # The frontmatter is available as a dictionary in post.metadata
        metadata = post.metadata

        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"Successfully extracted frontmatter to {args.output_json}")

    except Exception as e:
        print(f"Error processing {args.input_md}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
