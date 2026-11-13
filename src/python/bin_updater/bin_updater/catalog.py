import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path

import tomlkit
from pydantic import BaseModel, Field


class NonGitHubReleaseError(ValueError):
    """Raised when a tool catalog does not use GitHub releases."""


class ToolCatalog(BaseModel):
    name: str
    path: Path
    version: str
    repo: str
    tag_format: str = "v{version}"
    minimum_release_age: str | int | None = None
    platforms: Mapping[str, str]
    ext: Mapping[str, str] = Field(default_factory=dict)
    filename_format: str


def load_catalog(path: Path) -> ToolCatalog:
    """Load and validate tool catalog TOML file with GitHub releases configuration."""
    content = path.read_text(encoding="utf-8")
    data = tomllib.loads(content)
    bin_table = data.get("bin")
    if not isinstance(bin_table, Mapping) or not bin_table:
        raise ValueError(f"No [bin.<tool>] table found in {path}")
    name = next(iter(bin_table.keys()))
    tool_data = bin_table[name]
    if not isinstance(tool_data, Mapping):
        raise ValueError(f"Invalid [bin.{name}] section in {path}")
    gr = tool_data.get("github_releases")
    if not isinstance(gr, Mapping):
        raise NonGitHubReleaseError(f"No [bin.{name}.github_releases] table in {path}")
    repo = gr.get("repo")
    if not isinstance(repo, str) or not repo:
        raise ValueError(f"No repo specified in {path}")
    platforms = gr.get("platforms", {})
    if not isinstance(platforms, Mapping):
        raise ValueError(f"Invalid platforms mapping in {path}")
    ext_data = gr.get("ext", {})
    ext = ext_data if isinstance(ext_data, Mapping) else {}
    min_age = tool_data.get("minimum_release_age")
    if min_age is None:
        min_age = gr.get("minimum_release_age")
    return ToolCatalog(
        name=name,
        path=path,
        version=str(tool_data.get("version", "")),
        repo=repo,
        tag_format=str(gr.get("tag_format", "v{version}")),
        minimum_release_age=min_age,
        platforms={k: str(v) for k, v in platforms.items()},
        ext={k: str(v) for k, v in ext.items()},
        filename_format=str(gr.get("filename_format", "")),
    )


def discover_catalogs(directory: Path) -> Sequence[ToolCatalog]:
    """Find all valid tool catalogs with GitHub releases in target directory."""

    def _try_load(path: Path) -> ToolCatalog | None:
        try:
            return load_catalog(path)
        except NonGitHubReleaseError:
            return None

    return [cat for p in sorted(directory.glob("*.toml")) if (cat := _try_load(p)) is not None]


def update_catalog_content(content: str, new_version: str, new_checksums: Mapping[str, str]) -> str:
    """Update version and checksums in TOML string preserving comments and style."""
    doc = tomlkit.parse(content)
    bin_table = doc.get("bin")
    if not isinstance(bin_table, Mapping) or not bin_table:
        raise ValueError("Missing bin table in TOML content")
    name = next(iter(bin_table.keys()))
    doc["bin"][name]["version"] = new_version
    gr = doc["bin"][name]["github_releases"]
    if "checksums" not in gr:
        gr["checksums"] = tomlkit.table()
    for platform, sha in new_checksums.items():
        gr["checksums"][platform] = sha
    return tomlkit.dumps(doc)
