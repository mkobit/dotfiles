"""Validate data from the binary updater and publish catalog-only pull requests."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import quote

CATALOGS = Path("src/chezmoi/.chezmoidata/bin")
TOOL = re.compile(r"[a-z0-9][a-z0-9_-]*")
VERSION = re.compile(r"v?[0-9]{1,9}(?:\.[0-9]{1,9}){1,5}")
CHECKSUM = re.compile(r"[0-9a-f]{64}")
PR_BODY_LIMIT = 65536
AT_SIGN = re.compile(r"@|&(?:commat;|#(?:0*64(?![0-9])|[xX]0*40(?![0-9a-fA-F]));?)")
NOTE_TOKEN = re.compile(
    r"(?P<url>https?://[a-zA-Z0-9.\-]+(?::[0-9]+)?/[^\s<>\[\]()?#]*)"
    rf"|{AT_SIGN.pattern}"
)


def mute_mentions(body):
    def replace(match):
        if match.group("url"):
            # A malformed link can expose its path as text. Keep at signs inert there too.
            return AT_SIGN.sub("%40", match[0])
        return "@\u200b"

    return NOTE_TOKEN.sub(replace, body)


# Each selector matches the supported release series for this catalog pin.
MISE_TOOLS = {
    "bun": ("1", r"1\.[0-9]{1,9}\.[0-9]{1,9}", "https://bun.com/blog/bun-v{version}"),
    "java": (
        "temurin-21",
        r"temurin-(21\.[0-9]{1,9}\.[0-9]{1,9})\+([0-9]{1,9})\.0\.LTS",
        "https://adoptium.net/temurin/releases/?version=21",
    ),
    "node": ("22", r"22\.[0-9]{1,9}\.[0-9]{1,9}", "https://nodejs.org/en/blog/release/v{version}"),
    "ollama": (
        "0",
        r"0\.[0-9]{1,9}\.[0-9]{1,9}",
        "https://github.com/ollama/ollama/releases/tag/v{version}",
    ),
    "python": ("3.14", r"3\.14\.[0-9]{1,9}", "https://docs.python.org/release/{version}/whatsnew/changelog.html"),
}
OID = re.compile(r"[0-9a-f]{40}")


def version_key(version):
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Unsupported version format")
    parts = tuple(map(int, version.removeprefix("v").split(".")))
    return parts + (0,) * (6 - len(parts))


def catalog_fields(document, name):
    tool = document["bin"][name]
    source = "direct_release" if tool.get("updater", {}).get("source") == "claude" else "github_releases"
    return tool, source, tool[source]


def upstream_notes(original, name, new):
    if name.startswith("mise-") and (tool := name.removeprefix("mise-")) in MISE_TOOLS:
        return MISE_TOOLS[tool][2].format(version=new)
    fields, source, release = catalog_fields(tomllib.loads(original), name)
    metadata = fields["updater"] if source == "direct_release" else release
    return f"https://github.com/{quote(metadata['repo'], safe='/')}/releases"


def mise_version_key(tool, version):
    _, pattern, _ = MISE_TOOLS[tool]
    match = re.fullmatch(pattern, version) if isinstance(version, str) else None
    if match is None:
        raise ValueError("Expected a stable version within the supported mise release series")
    numeric = ".".join(match.groups()) if tool == "java" else version
    return version_key(numeric)


def with_mise_version(document, tool, version):
    fields = document["mise"]["global_tools"][tool]
    old_version = fields["version"]
    fields["version"] = version
    return old_version, {f"mise.global_tools.{tool}": {"version": version}}


def approved_catalog(base, candidate, name):
    original = tomllib.loads(base)
    proposed = tomllib.loads(candidate)
    tool = name.removeprefix("mise-")
    if name.startswith("mise-") and tool in MISE_TOOLS:
        new = proposed["mise"]["global_tools"][tool]["version"]
        old, replacements = with_mise_version(original, tool, new)
        if mise_version_key(tool, new) <= mise_version_key(tool, old):
            raise ValueError("Expected a forward mise version")
        if original != proposed:
            raise ValueError("Catalog edit exceeds the selected mise version field")
        return rebuild_catalog(base, original, replacements), old, new
    return approved_binary_catalog(base, original, proposed, name)


def approved_binary_catalog(base, original, proposed, name):
    old, source, release = catalog_fields(original, name)
    new, _, new_release = catalog_fields(proposed, name)
    old_version = old["version"]
    new_version = new["version"]
    if version_key(new_version) <= version_key(old_version) or old_version.startswith("v") != new_version.startswith(
        "v"
    ):
        raise ValueError("Expected a forward version with the existing prefix convention")
    hashes = new_release["checksums"]
    if (
        not isinstance(hashes, dict)
        or not release["platforms"]
        or set(hashes) != set(release["platforms"])
        or any(not isinstance(digest, str) or not CHECKSUM.fullmatch(digest) for digest in hashes.values())
    ):
        raise ValueError("Expected a SHA-256 checksum for each configured platform")
    old["version"] = new_version
    release["checksums"] = hashes
    if original != proposed:
        raise ValueError("Catalog edit exceeds version and checksum fields")

    replacements = {f"bin.{name}": {"version": new_version}, f"bin.{name}.{source}.checksums": hashes.copy()}
    return rebuild_catalog(base, original, replacements), old_version, new_version


def rebuild_catalog(base, expected, replacements):
    # Rebuild from trusted bytes so generated TOML syntax never reaches Git.
    table = ""
    lines = []
    for line in base.splitlines(keepends=True):
        header = re.fullmatch(r"\s*\[([^\[\]]+)\]\s*(?:#.*)?\n?", line)
        if header:
            table = header[1]
        assignment = re.fullmatch(r'([ \t]*([\w-]+)[ \t]*=[ \t]*)"[^"]*"([^\n]*)(\n?)', line)
        fields = replacements.get(table, {})
        if assignment and assignment[2] in fields:
            lines.append(f'{assignment[1]}"{fields.pop(assignment[2])}"{assignment[3]}{assignment[4]}')
        else:
            lines.append(line)
    rebuilt = "".join(lines)
    if any(replacements.values()) or tomllib.loads(rebuilt) != expected:
        raise ValueError("Unsupported trusted catalog layout")
    return rebuilt


def command(*args, stdin=None, env=None):
    return subprocess.run(args, input=stdin, env=env, text=True, stdout=subprocess.PIPE, check=True).stdout


def remote_tip(ref):
    output = command("git", "ls-remote", "--refs", "origin", ref)
    if not output:
        return ""
    sha, found_ref = output.strip().split("\t")
    if found_ref != ref or not OID.fullmatch(sha):
        raise ValueError("Unexpected remote ref")
    return sha


def update_branch(name, catalog, approved, base, directory, expected_pr_head=None):
    branch = f"automation/bin-update-{name}"
    ref = f"refs/heads/{branch}"
    inspected = remote_tip(ref)
    if expected_pr_head is not None and inspected != expected_pr_head:
        raise ValueError("Existing PR head changed before branch update")
    if inspected:
        command("git", "fetch", "--no-tags", "origin", ref)
        if command("git", "rev-parse", "FETCH_HEAD").strip() != inspected:
            raise ValueError("Update branch changed while inspecting it")
        common = command("git", "merge-base", base, inspected).strip()
        if command("git", "diff", "--name-only", common, inspected).splitlines() != [catalog.as_posix()]:
            raise ValueError("Existing update branch contains unrelated changes")
        tree_entry = command("git", "ls-tree", inspected, "--", str(catalog))
        if not tree_entry.startswith("100644 blob "):
            raise ValueError("Existing catalog is not a regular file with the expected mode")
        previous = command("git", "show", f"{common}:{catalog}")
        existing = command("git", "show", f"{inspected}:{catalog}")
        if approved_catalog(previous, existing, name)[0] != existing:
            raise ValueError("Existing update branch does not contain a validated catalog")
        if common == base and existing == approved:
            return branch, inspected

    if remote_tip("refs/heads/main") != base:
        raise ValueError("Main changed after generation")
    index_env = {**os.environ, "GIT_INDEX_FILE": str(directory / "index")}
    command("git", "read-tree", base, env=index_env)
    blob = command("git", "hash-object", "-w", "--stdin", stdin=approved).strip()
    command("git", "update-index", "--cacheinfo", f"100644,{blob},{catalog}", env=index_env)
    tree = command("git", "write-tree", env=index_env).strip()
    if command("git", "diff", "--name-only", base, tree).splitlines() != [catalog.as_posix()]:
        raise ValueError("Candidate commit contains unexpected changes")
    commit = command(
        "git",
        "-c",
        "user.name=github-actions[bot]",
        "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit-tree",
        tree,
        "-p",
        base,
        "-m",
        f"Update {name}",
    ).strip()
    command(
        "git",
        "-c",
        "credential.helper=",
        "-c",
        "credential.helper=!gh auth git-credential",
        "push",
        f"--force-with-lease={ref}:{inspected}",
        "origin",
        f"{commit}:{ref}",
    )
    return branch, commit


def publish(name, artifact, base, repo):
    tool = name.removeprefix("mise-")
    catalog_name = "mise" if name.startswith("mise-") and tool in MISE_TOOLS else name
    catalog = CATALOGS / f"{catalog_name}.toml"
    original = command("git", "show", f"{base}:{catalog}")
    updated = (artifact / f"{name}.toml").read_text(encoding="utf-8")
    approved, old, new = approved_catalog(original, updated, name)
    report = json.loads((artifact / f"{name}.json").read_text(encoding="utf-8"))
    title = f"Update {name} from {old} to {new}"
    if not isinstance(report, list) or len(report) != 1 or not isinstance(report[0], dict):
        raise ValueError("Expected one update report")
    row = report[0]
    body = row.get("pr_body")
    if (
        row.get("changed") is not True
        or row.get("error") is not None
        or row.get("tool_name") != name
        or row.get("old_version") != old
        or row.get("new_version") != new
        or row.get("pr_title") != title
        or not isinstance(body, str)
        or not body
    ):
        raise ValueError("Update report does not match the catalog")
    preview = mute_mentions(body)
    if max(len(body), len(preview)) > PR_BODY_LIMIT:
        # Put the link before the notes so cut Markdown cannot hide it.
        url = upstream_notes(original, name, new)
        intro = f"Release notes preview. [Read the full upstream release notes]({url}).\n\n"
        preview = intro + preview[: PR_BODY_LIMIT - len(intro)].rstrip()
    body = preview
    branch = f"automation/bin-update-{name}"
    prior = open_pr(repo, branch)
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        branch, head = update_branch(name, catalog, approved, base, directory, prior["head"]["sha"] if prior else None)
        if remote_tip(f"refs/heads/{branch}") != head or remote_tip("refs/heads/main") != base:
            raise ValueError("PR base or head changed before publication")
        current = open_pr(repo, branch)
        if current:
            if current["head"]["sha"] != head or (prior and prior["number"] != current["number"]):
                raise ValueError("Existing PR changed before publication")
            payload = json.dumps({"title": title, "body": body})
            command(
                "gh",
                "api",
                "--method",
                "PATCH",
                f"repos/{repo}/pulls/{current['number']}",
                "--input",
                "-",
                stdin=payload,
            )
        elif prior:
            raise ValueError("Existing PR closed before publication")
        else:
            body_file = directory / "body.md"
            body_file.write_text(body, encoding="utf-8")
            command(
                "gh",
                "pr",
                "create",
                "--repo",
                repo,
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                title,
                "--body-file",
                str(body_file),
            )


def open_pr(repo, branch):
    prs = json.loads(
        command(
            "gh",
            "api",
            "--method",
            "GET",
            f"repos/{repo}/pulls",
            "-f",
            "state=open",
            "-f",
            "base=main",
            "-f",
            f"head={repo.split('/')[0]}:{branch}",
        )
    )
    if not prs:
        return None
    if len(prs) != 1 or prs[0]["auto_merge"] is not None:
        raise ValueError("Existing update branch has an ambiguous PR or pending automatic merge")
    return prs[0]


def generate_mise_updates(artifact, target):
    source = command("git", "show", f"HEAD:{CATALOGS / 'mise.toml'}")
    tools = MISE_TOOLS if target == "all" else (target.removeprefix("mise-"),)
    for tool in tools:
        name = f"mise-{tool}"
        try:
            selector, _, source_url = MISE_TOOLS[tool]
            document = tomllib.loads(source)
            age = document["mise"]["updates"]["minimum_release_age"]
            new = command("mise", "latest", "--minimum-release-age", age, f"{tool}@{selector}").strip()
            old, replacements = with_mise_version(document, tool, new)
            if mise_version_key(tool, new) <= mise_version_key(tool, old):
                continue
            updated = rebuild_catalog(source, document, replacements)
            title = f"Update {name} from {old} to {new}"
            report = [
                {
                    "tool_name": name,
                    "changed": True,
                    "old_version": old,
                    "new_version": new,
                    "pr_title": title,
                    "pr_body": f"Update {tool} from {old} to {new}.\n\n[Upstream releases]({source_url.format(version=new)})\n",
                }
            ]
            (artifact / f"{name}.toml").write_text(updated, encoding="utf-8")
            (artifact / f"{name}.json").write_text(json.dumps(report), encoding="utf-8")
        except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
            print(f"Generation failed for {name}: {error}", file=sys.stderr)
            with (artifact / "failures.txt").open("a", encoding="utf-8") as log:
                print(name, file=log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--generate-mise", choices=["all", *(f"mise-{tool}" for tool in MISE_TOOLS)])
    args = parser.parse_args()
    artifact = args.artifact
    if args.generate_mise is not None:
        generate_mise_updates(artifact, args.generate_mise)
        return 0
    repo = os.environ["GITHUB_REPOSITORY"]
    base = os.environ["GITHUB_SHA"]
    if not os.environ.get("GH_TOKEN", ""):
        parser.error("The publication credential is missing")
    if not OID.fullmatch(base) or command("git", "rev-parse", "HEAD").strip() != base:
        parser.error("Publication must use the workflow commit")
    if remote_tip("refs/heads/main") != base:
        parser.error("Generation did not use current main")
    if artifact.is_symlink() or not artifact.is_dir():
        parser.error("Expected an update artifact directory")
    entries = list(artifact.iterdir())
    pairs = {}
    for path in entries:
        if path.name == "failures.txt" and path.is_file() and not path.is_symlink():
            continue
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size > 512_000
            or path.suffix not in {".toml", ".json"}
            or not TOOL.fullmatch(path.stem)
        ):
            parser.error("Unexpected update artifact entry")
        pairs.setdefault(path.stem, set()).add(path.suffix)
    if any(suffixes != {".toml", ".json"} for suffixes in pairs.values()):
        parser.error("Incomplete update artifact")
    failed = False
    for name in sorted(pairs):
        try:
            publish(name, artifact, base, repo)
        except ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError:
            print(f"Publication failed for {name}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
