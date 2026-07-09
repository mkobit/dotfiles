from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SandboxSpec:
    home: Path
    project_root: Path
    project_write: bool
    profile_name: str
    cwd: Path
    git_common_dir: Path | None = None
    extra_env: dict[str, str] = field(default_factory=dict)
    tty: bool = False
    network: str = "shared"
    ssh_agent_sock: Path | None = None
    gpg_agent_sock: Path | None = None
    extra_ro: tuple[Path, ...] = ()
    extra_rw: tuple[Path, ...] = ()
    home_rw: tuple[str, ...] = ()
    home_mask: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
