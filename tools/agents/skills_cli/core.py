"""Shared logic for skill discovery, sync, and drift checking."""

import filecmp
import shutil
import subprocess
from pathlib import Path

from tools.agents.skills_cli.models import DriftResult, SkillSource, SyncResult


def discover_tools(chezmoi_dir: Path) -> list[str]:
    """Find target tool names from dot_*/skills/ directories.

    Args:
        chezmoi_dir: Path to the chezmoi source directory (e.g., src/chezmoi).

    Returns:
        Sorted list of tool names (e.g., ["claude", "cursor", "gemini"]).
    """
    tools: list[str] = []
    for skills_dir in sorted(chezmoi_dir.glob("dot_*/skills")):
        if skills_dir.is_dir():
            tool = skills_dir.parent.name.removeprefix("dot_")
            tools.append(tool)
    return tools


def discover_local_skills(canonical_dir: Path) -> list[SkillSource]:
    """Find local skills from the canonical directory.

    Args:
        canonical_dir: Path to src/agents/skills/.

    Returns:
        List of SkillSource entries for each skill with a SKILL.md.
    """
    skills: list[SkillSource] = []
    if not canonical_dir.is_dir():
        return skills
    for skill_dir in sorted(canonical_dir.iterdir()):
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
            skills.append(
                SkillSource(name=skill_dir.name, path=skill_dir, origin="local")
            )
    return skills


def _dirs_match(source: Path, target: Path) -> bool:
    """Recursively compare two directories for equality.

    Uses filecmp.dircmp to compare file contents, not just metadata.
    """
    cmp = filecmp.dircmp(str(source), str(target))
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    # dircmp uses shallow comparison by default; do a deep compare on common files
    _, mismatches, errors = filecmp.cmpfiles(
        str(source), str(target), cmp.common_files, shallow=False
    )
    if mismatches or errors:
        return False
    # Recurse into subdirectories
    for subdir in cmp.common_dirs:
        if not _dirs_match(source / subdir, target / subdir):
            return False
    return True


def _diff_details(source: Path, target: Path) -> str:
    """Generate a human-readable diff summary between two directories."""
    try:
        result = subprocess.run(
            ["diff", "-r", str(source), str(target)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout or result.stderr
    except FileNotFoundError:
        return f"{source} vs {target}: diff command not available"


def sync_skill(source: Path, target: Path) -> bool:
    """Sync a skill directory from source to target.

    Compares directories and copies if different.
    Follows symlinks (matching cp -RL behavior).

    Args:
        source: Source skill directory.
        target: Target skill directory.

    Returns:
        True if the target was updated, False if already up to date.
    """
    if target.is_dir() and _dirs_match(source, target):
        return False

    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, symlinks=False, copy_function=shutil.copy2)
    return True


def check_skill(source: Path, target: Path) -> DriftResult:
    """Check a skill directory for drift.

    Args:
        source: Source (canonical) skill directory.
        target: Target (committed copy) skill directory.

    Returns:
        DriftResult with drift status and details.
    """
    skill_name = source.name
    tool_name = ""  # Filled by caller via the result

    if not target.is_dir():
        return DriftResult(
            skill=skill_name,
            tool=tool_name,
            drifted=True,
            details=f"MISSING: {target} (expected copy of {source})",
        )

    if not _dirs_match(source, target):
        details = _diff_details(source, target)
        return DriftResult(
            skill=skill_name,
            tool=tool_name,
            drifted=True,
            details=f"DRIFT: {target} differs from {source}\n{details}",
        )

    return DriftResult(skill=skill_name, tool=tool_name, drifted=False)


def sync_all(workspace: Path, verbose: bool = False) -> tuple[list[SyncResult], bool]:
    """Sync all skills to all tool directories.

    Args:
        workspace: Path to the workspace root (BUILD_WORKSPACE_DIRECTORY).
        verbose: Print progress messages.

    Returns:
        Tuple of (list of sync results, success flag).
    """
    chezmoi_dir = workspace / "src" / "chezmoi"
    canonical_dir = workspace / "src" / "agents" / "skills"

    tools = discover_tools(chezmoi_dir)
    if not tools:
        if verbose:
            print(
                "No target tool directories found "
                f"(expected {chezmoi_dir}/dot_*/skills/)."
            )
        return [], False

    if verbose:
        print(f"Target tools: {', '.join(tools)}")

    results: list[SyncResult] = []

    # Local skills
    for skill in discover_local_skills(canonical_dir):
        for tool in tools:
            target = chezmoi_dir / f"dot_{tool}" / "skills" / skill.name
            updated = sync_skill(skill.path, target)
            action: str = "synced" if updated else "up_to_date"
            if updated and not target.exists():
                action = "created"
            results.append(SyncResult(skill=skill.name, tool=tool, action=action))
            if verbose and updated:
                print(f"  Synced (local): {skill.name} -> {tool}")

    return results, True


def check_all(workspace: Path, verbose: bool = False) -> tuple[list[DriftResult], bool]:
    """Check all skills for drift.

    Args:
        workspace: Path to the workspace root (BUILD_WORKSPACE_DIRECTORY).
        verbose: Print progress messages.

    Returns:
        Tuple of (list of drift results, success flag — False if drift found).
    """
    chezmoi_dir = workspace / "src" / "chezmoi"
    canonical_dir = workspace / "src" / "agents" / "skills"

    tools = discover_tools(chezmoi_dir)
    if not tools:
        if verbose:
            print(
                "No target tool directories found "
                f"(expected {chezmoi_dir}/dot_*/skills/)."
            )
        return [], False

    results: list[DriftResult] = []
    drift_found = False

    # Local skills
    for skill in discover_local_skills(canonical_dir):
        for tool in tools:
            target = chezmoi_dir / f"dot_{tool}" / "skills" / skill.name
            result = check_skill(skill.path, target)
            result.tool = tool
            result.skill = skill.name
            results.append(result)
            if result.drifted:
                drift_found = True
                if verbose:
                    print(f"  {result.details}")

    return results, not drift_found
