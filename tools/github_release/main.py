import asyncio
import sys
from pathlib import Path
import tomllib
import toml

import aiohttp
import click

from tools.github_release.lib import (
    generate_chezmoi_external,
    get_asset_sha256,
    get_release_info,
    select_asset,
)


@click.command()
@click.option("--repo", required=True, help="GitHub repository in 'owner/repo' format.")
@click.option("--version", required=True, help="Release version/tag (or 'latest').")
@click.option("--dest", required=True, help="Destination path for the extracted file in chezmoi.")
@click.option("--asset-glob", required=True, help="Regex pattern to select the release asset.")
@click.option("--output", required=True, type=click.Path(), help="Output file path, or '-' for stdout.")
@click.option(
    "--check",
    is_flag=True,
    help="Check if the file is up-to-date and exit with an error if not.",
)
def main(repo, version, dest, asset_glob, output, check):
    """Fetch GitHub release info and generate chezmoi external data."""
    async def async_main():
        async with aiohttp.ClientSession() as session:
            try:
                release_info = await get_release_info(session, repo, version)
                selected_asset = select_asset(release_info["assets"], asset_glob)

                if not selected_asset:
                    click.echo(f"Error: No asset found for repo '{repo}' with glob '{asset_glob}'", err=True)
                    sys.exit(1)

                asset_url = selected_asset["browser_download_url"]
                sha256 = await get_asset_sha256(session, asset_url)

                generated_data = {dest: generate_chezmoi_external(asset_url, sha256)}

                if check:
                    if output == "-":
                        click.echo("Error: --check cannot be used with stdout.", err=True)
                        sys.exit(1)

                    output_path = Path(output)
                    if not output_path.exists():
                        click.echo(f"Error: --check failed because file does not exist: {output_path}", err=True)
                        sys.exit(1)

                    with open(output_path, "rb") as f:
                        existing_data = tomllib.load(f)

                    if existing_data == generated_data:
                        click.echo(f"Success: {output_path} is up-to-date.", err=True)
                        sys.exit(0)
                    else:
                        click.echo(f"Error: {output_path} is out of date.", err=True)
                        sys.exit(1)
                else:
                    if output == "-":
                        sys.stdout.write(toml.dumps(generated_data))
                    else:
                        output_path = Path(output)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "w") as f:
                            toml.dump(generated_data, f)
                        click.echo(f"Successfully generated chezmoi external for {dest} at {output_path}", err=True)

            except aiohttp.ClientError as e:
                click.echo(f"Error fetching data from GitHub: {e}", err=True)
                sys.exit(1)
            except Exception as e:
                click.echo(f"An unexpected error occurred: {e}", err=True)
                sys.exit(1)

    asyncio.run(async_main())

if __name__ == "__main__":
    main()
