import argparse
import sys
from pathlib import Path
import tomllib
import tomli_w

from tools.github_release.lib import (
    generate_chezmoi_external,
    get_asset_sha256,
    get_release_info,
    select_asset,
)


def main():
    """Fetch GitHub release info and generate chezmoi external data."""
    parser = argparse.ArgumentParser(description="Fetch GitHub release info and generate chezmoi external data.")
    parser.add_argument("--repo", required=True, help="GitHub repository in 'owner/repo' format.")
    parser.add_argument("--version", required=True, help="Release version/tag (or 'latest').")
    parser.add_argument("--dest", required=True, help="Destination path for the extracted file in chezmoi.")
    parser.add_argument("--asset-glob", required=True, help="Regex pattern to select the release asset.")
    parser.add_argument("--output", required=True, type=Path, help="Output file path.")
    args = parser.parse_args()

    try:
        release_info = get_release_info(args.repo, args.version)
        selected_asset = select_asset(release_info["assets"], args.asset_glob)

        if not selected_asset:
            print(f"Error: No asset found for repo '{args.repo}' with glob '{args.asset_glob}'", file=sys.stderr)
            sys.exit(1)

        asset_url = selected_asset["browser_download_url"]
        sha256 = get_asset_sha256(asset_url)

        generated_data = {args.dest: generate_chezmoi_external(asset_url, sha256)}

        with open(args.output, "wb") as f:
            tomli_w.dump(generated_data, f)

        print(f"Successfully generated chezmoi external for {args.dest} at {args.output}", file=sys.stderr)

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()