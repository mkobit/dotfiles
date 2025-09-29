import asyncio
import sys
from pathlib import Path
import tomllib
import toml

import aiohttp
import click

from tools.github_release.lib import (
    ChezmoiData,
    GitHubAsset,
    extract_arch_os,
    get_asset_sha256,
    get_checksums_from_file,
    get_release_info,
)


@click.command()
@click.option("--repo", required=True, help="GitHub repository in 'owner/repo' format.")
@click.option("--version", required=True, help="Release version/tag (or 'latest').")
@click.option("--tool-name", required=True, help="Name of the tool for the TOML file.")
@click.option("--output", required=True, type=click.Path(), help="Output file path, or '-' for stdout.")
@click.option(
    "--check",
    is_flag=True,
    help="Check if the file is up-to-date and exit with an error if not.",
)
def main(repo, version, tool_name, output, check):
    """Fetch GitHub release info and generate chezmoi data."""
    async def async_main():
        async with aiohttp.ClientSession() as session:
            try:
                release_info = await get_release_info(session, repo, version)
                assets: list[GitHubAsset] = release_info["assets"]
                release_version = release_info["tag_name"]
                checksums = {}

                checksum_asset = next((a for a in assets if "checksum" in a["name"].lower() or "sha256" in a["name"].lower()), None)

                if checksum_asset:
                    click.echo(f"Found checksum file: {checksum_asset['name']}", err=True)
                    checksums_from_file = await get_checksums_from_file(session, checksum_asset["browser_download_url"])
                else:
                    checksums_from_file = {}

                for asset in assets:
                    arch_os = extract_arch_os(asset["name"])
                    if not arch_os:
                        continue

                    if asset["name"] in checksums_from_file:
                        sha256 = checksums_from_file[asset["name"]]
                        click.echo(f"Found SHA for {asset['name']} in checksum file.", err=True)
                    else:
                        click.echo(f"Calculating SHA for {asset['name']} by downloading.", err=True)
                        sha256 = await get_asset_sha256(session, asset["browser_download_url"])

                    checksums[arch_os] = sha256

                generated_data: ChezmoiData = {
                    "version": release_version,
                    "checksums": checksums,
                }

                final_toml_data = {tool_name: generated_data}

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

                    if existing_data == final_toml_data:
                        click.echo(f"Success: {output_path} is up-to-date.", err=True)
                        sys.exit(0)
                    else:
                        click.echo(f"Error: {output_path} is out of date.", err=True)
                        sys.exit(1)
                else:
                    if output == "-":
                        sys.stdout.write(toml.dumps(final_toml_data))
                    else:
                        output_path = Path(output)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "w") as f:
                            toml.dump(final_toml_data, f)
                        click.echo(f"Successfully generated chezmoi data for {tool_name} {release_version} at {output_path}", err=True)

            except aiohttp.ClientError as e:
                click.echo(f"Error fetching data from GitHub: {e}", err=True)
                sys.exit(1)
            except Exception as e:
                click.echo(f"An unexpected error occurred: {e}", err=True)
                sys.exit(1)

    asyncio.run(async_main())

if __name__ == "__main__":
    main()