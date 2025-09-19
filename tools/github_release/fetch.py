import argparse
import asyncio
import sys
from pathlib import Path

import aiohttp
import toml

from tools.github_release.lib import (
    generate_toml_dict,
    get_asset_sha256,
    get_release_info,
    select_asset,
)


async def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub release info and generate chezmoi data.")
    parser.add_argument("--repo", required=True, help="GitHub repository in 'owner/repo' format.")
    parser.add_argument("--version", required=True, help="Release version/tag (or 'latest').")
    parser.add_argument("--tool-name", required=True, help="Name of the tool for the TOML file.")
    parser.add_argument("--output", required=True, type=str, help="Output file path, or '-' for stdout.")
    parser.add_argument(
        "--asset-glob",
        default=r".*linux-amd64\.tar\.gz",
        help="Regex pattern to select the release asset.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if the file is up-to-date and exit with an error if not.",
    )

    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        try:
            release_info = await get_release_info(session, args.repo, args.version)
            selected_asset = select_asset(release_info["assets"], args.asset_glob)

            if not selected_asset:
                print(f"Error: No asset found for repo '{args.repo}' with glob '{args.asset_glob}'", file=sys.stderr)
                sys.exit(1)

            asset_url = selected_asset["browser_download_url"]
            asset_name = selected_asset["name"]
            sha256 = await get_asset_sha256(session, asset_url)
            version = release_info["tag_name"]

            generated_data = {args.tool_name: generate_toml_dict(version, sha256, asset_url, asset_name)}

            if args.check:
                if args.output == "-":
                    print("Error: --check cannot be used with stdout.", file=sys.stderr)
                    sys.exit(1)

                output_path = Path(args.output)
                if not output_path.exists():
                    print(f"Error: --check failed because file does not exist: {output_path}", file=sys.stderr)
                    sys.exit(1)

                existing_data = toml.load(output_path)
                if existing_data == generated_data:
                    print(f"Success: {output_path} is up-to-date.")
                    sys.exit(0)
                else:
                    print(f"Error: {output_path} is out of date.", file=sys.stderr)
                    sys.exit(1)
            else:
                if args.output == "-":
                    toml.dump(generated_data, sys.stdout)
                else:
                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w") as f:
                        toml.dump(generated_data, f)
                    print(f"Successfully generated chezmoi data for {args.tool_name} {version} at {output_path}")

        except aiohttp.ClientError as e:
            print(f"Error fetching data from GitHub: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
