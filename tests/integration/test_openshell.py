import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml
from chezmoi_test_data import installation_method

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
OPENSHELL_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "bin" / "openshell.toml"
BIN_UPDATES_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "bin-updates.toml"
OPENSHELL_DOCTOR_TEMPLATE = CHEZMOI_SOURCE / "dot_local" / "bin" / "executable_openshell-doctor.tmpl"
BINS_EXTERNAL_TEMPLATE = CHEZMOI_SOURCE / "dot_local" / "bin" / ".chezmoiexternals" / "bins.toml.tmpl"
BASH_CONFIG_TEMPLATE = CHEZMOI_SOURCE / "dot_dotfiles" / "bash" / "config.bash.tmpl"
ZSH_CONFIG_TEMPLATE = CHEZMOI_SOURCE / "dot_dotfiles" / "zsh" / "config.zsh.tmpl"
SANDBOX_GITCONFIG_TEMPLATE = CHEZMOI_SOURCE / "dot_config" / "ai-policy" / "git" / "sandbox.gitconfig.tmpl"
SANDBOX_CHEZMOI_CONFIG = REPO_ROOT / "docker" / "openshell" / "sandbox-chezmoi.toml"
SANDBOX_DOCKERFILE = REPO_ROOT / "docker" / "openshell" / "Dockerfile"
GITHUB_PUSH_POLICY = REPO_ROOT / "docker" / "openshell" / "github-push.yaml"
OPENSHELL_SKILL_DIR = (
    CHEZMOI_SOURCE
    / "dot_local"
    / "share"
    / "agent-plugins"
    / "marketplace"
    / "exact_plugins"
    / "exact_mkobit-dotfiles"
    / "exact_skills"
    / "exact_openshell-sandboxes"
)
OPENSHELL_BOOTSTRAP_DOC = REPO_ROOT / "docs" / "openshell-bootstrap.md"


def test_openshell_release_catalog_pins_v0_1_9_with_verified_checksums() -> None:
    """Keep the OpenShell release archive pinned to the verified v0.1.9 assets."""
    with OPENSHELL_CATALOG.open("rb") as catalog_file:
        catalog = tomllib.load(catalog_file)

    openshell = catalog["bin"]["openshell"]
    assert openshell["version"] == "0.1.9"
    gr = openshell["github_releases"]
    assert gr["repo"] == "NVIDIA/OpenShell"
    assert gr["external_type"] == "archive-file"
    assert gr["executable"] is True
    assert gr["checksum_type"] == "sha256"
    assert gr["tag_format"] == "v{version}"
    assert gr["filename_format"] == "openshell-{target}.tar.gz"
    assert gr["path_format"] == "openshell"
    assert gr["url_format"] == "{base}/{repo}/releases/download/{tag}/{filename}"
    assert gr["platforms"] == {
        "darwin_arm64": "aarch64-apple-darwin",
        "linux_amd64": "x86_64-unknown-linux-musl",
        "linux_arm64": "aarch64-unknown-linux-musl",
    }
    assert gr["checksums"] == {
        "darwin_arm64": "355bf612159eaa0c5375facd8f27536d9cb54e5af030328ea839a927a7901da5",
        "linux_amd64": "3856ac7b6b2e33d6c8ab72a1036444156516e7303da85a9b13f661a2aa63bd2d",
        "linux_arm64": "cb923d08703b966f7e0e6b1483ed4ba6ed77bc10812c5502bcc1fb6ee0f6ad59",
    }


def test_openshell_bin_updates_policy_declares_10d_cooldown() -> None:
    with BIN_UPDATES_CATALOG.open("rb") as updates_file:
        updates = tomllib.load(updates_file)

    tools = updates["bin_updates"]["tools"]
    assert tools["openshell"] == "10d"
    assert list(tools.keys()) == sorted(tools.keys())


@pytest.mark.parametrize(
    ("system", "arch", "expected_method", "expected_target"),
    [
        ("linux", "amd64", "github_releases", "x86_64-unknown-linux-musl"),
        ("linux", "arm64", "github_releases", "aarch64-unknown-linux-musl"),
        ("linux", "386", "none", ""),
        ("darwin", "arm64", "github_releases", "aarch64-apple-darwin"),
        ("darwin", "amd64", "none", ""),
        ("windows", "amd64", "none", ""),
        ("freebsd", "amd64", "none", ""),
    ],
)
def test_openshell_init_selects_supported_installation(
    tmp_path: Path,
    system: str,
    arch: str,
    expected_method: str,
    expected_target: str,
) -> None:
    sw_vers = tmp_path / "sw_vers"
    sw_vers.write_text('#!/bin/sh\nprintf "15.7.1\\n"\n', encoding="utf-8")
    sw_vers.chmod(0o755)
    chezmoi = shutil.which("chezmoi")
    assert chezmoi is not None
    config = tmp_path / "config.toml"
    platform = {"chezmoi": {"os": system, "arch": arch}}
    initialized = subprocess.run(
        [
            chezmoi,
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            "--destination",
            str(tmp_path),
            "execute-template",
            "--init",
            "--override-data",
            json.dumps(platform),
            "--file",
            str(CHEZMOI_SOURCE / ".chezmoi.toml.tmpl"),
        ],
        env={**os.environ, "CI": "1", "PATH": f"{tmp_path}:{os.defpath}"},
        capture_output=True,
        text=True,
        check=True,
    )
    config.write_text(initialized.stdout, encoding="utf-8")
    data = tomllib.loads(initialized.stdout)["data"]
    assert data["local"]["bin"]["openshell"]["installation_method"] == expected_method

    def render(template_path: Path, extra_override: dict | None = None) -> str:
        override = {**platform, **(extra_override or {})}
        result = subprocess.run(
            [
                chezmoi,
                "--config",
                str(config),
                "--source",
                str(REPO_ROOT),
                "--destination",
                str(tmp_path),
                "execute-template",
                "--override-data",
                json.dumps(override),
                "--file",
                str(template_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    if expected_method == "github_releases":
        externals = tomllib.loads(render(BINS_EXTERNAL_TEMPLATE))
        assert "openshell" in externals
        entry = externals["openshell"]
        assert entry["type"] == "archive-file"
        assert entry["executable"] is True
        assert entry["path"] == "openshell"
        assert entry["url"].endswith(f"/v0.1.9/openshell-{expected_target}.tar.gz")
        disabled_externals = tomllib.loads(
            render(
                BINS_EXTERNAL_TEMPLATE,
                {"local": {"bin": {"openshell": {"installation_method": "none"}}}},
            )
        )
        assert "openshell" not in disabled_externals


def _render_template(
    template_path: Path,
    override_data: dict,
    destination: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            *(["--destination", str(destination)] if destination is not None else []),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(override_data),
            str(template_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def test_openshell_shell_completions_render_only_when_enabled() -> None:
    enabled_override = {"local": {"bin": {"openshell": {"installation_method": "github_releases"}}}}
    disabled_override = {"local": {"bin": {"openshell": {"installation_method": "none"}}}}

    bash_enabled = _render_template(BASH_CONFIG_TEMPLATE, enabled_override)
    assert bash_enabled.returncode == 0, bash_enabled.stderr
    assert 'eval "$(openshell completions bash)"' in bash_enabled.stdout

    zsh_enabled = _render_template(ZSH_CONFIG_TEMPLATE, enabled_override)
    assert zsh_enabled.returncode == 0, zsh_enabled.stderr
    assert 'eval "$(openshell completions zsh)"' in zsh_enabled.stdout

    bash_disabled = _render_template(BASH_CONFIG_TEMPLATE, disabled_override)
    assert bash_disabled.returncode == 0, bash_disabled.stderr
    assert "openshell completions" not in bash_disabled.stdout

    zsh_disabled = _render_template(ZSH_CONFIG_TEMPLATE, disabled_override)
    assert zsh_disabled.returncode == 0, zsh_disabled.stderr
    assert "openshell completions" not in zsh_disabled.stdout

    missing_bash = _render_template(BASH_CONFIG_TEMPLATE, {})
    assert missing_bash.returncode == 0, missing_bash.stderr
    assert "openshell completions" not in missing_bash.stdout


def test_openshell_doctor_renders_only_when_enabled(tmp_path: Path) -> None:
    disabled = _render_template(
        OPENSHELL_DOCTOR_TEMPLATE,
        {"local": {"bin": {"openshell": {"installation_method": "none"}}}},
        destination=tmp_path,
    )
    assert disabled.returncode == 0, disabled.stderr
    assert disabled.stdout == ""

    missing = _render_template(OPENSHELL_DOCTOR_TEMPLATE, {}, destination=tmp_path)
    assert missing.returncode == 0, missing.stderr
    assert missing.stdout == ""

    enabled = _render_template(
        OPENSHELL_DOCTOR_TEMPLATE,
        {"local": {"bin": {"openshell": {"installation_method": "github_releases"}}}},
        destination=tmp_path,
    )
    assert enabled.returncode == 0, enabled.stderr
    assert f'export PATH="{tmp_path}/.local/bin:${{PATH}}"' in enabled.stdout
    assert "$HOME" not in enabled.stdout


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.parametrize("microvm", [False, True], ids=["active-gateway", "microvm-gateway"])
def test_openshell_doctor_passes_and_redacts_provider_output(tmp_path: Path, *, microvm: bool) -> None:
    rendered = _render_template(
        OPENSHELL_DOCTOR_TEMPLATE,
        {
            "chezmoi": {"os": "linux", "arch": "amd64", "username": "mkobit"},
            "local": {"bin": {"openshell": {"installation_method": "github_releases", "microvm": microvm}}},
        },
        destination=tmp_path,
    )
    assert rendered.returncode == 0, rendered.stderr

    bin_dir = tmp_path / ".local" / "bin"
    bin_dir.mkdir(parents=True)

    gateway_arg = " -g openshell-microvm" if microvm else ""
    _write_executable(
        bin_dir / "openshell",
        "#!/bin/sh\n"
        'case "$*" in\n'
        "  --version) echo 'openshell 0.1.9' ;;\n"
        f"  'status{gateway_arg}'|'gateway info{gateway_arg}') exit 0 ;;\n"
        f"  'provider list{gateway_arg}')\n"
        "    printf 'NAME   PROVIDER   SECRET\\ngithub github     ghp_SUPER_SECRET_TOKEN_VALUE_12345\\n'\n"
        "    ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
    )
    _write_executable(
        bin_dir / "docker",
        "#!/bin/sh\nif [ \"$1\" = 'info' ]; then\n  echo 'Security Options: rootless'\n  exit 0\nfi\nexit 1\n",
    )
    _write_executable(
        bin_dir / "loginctl",
        "#!/bin/sh\necho 'yes'\n",
    )

    env = {**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin", "USER": "mkobit"}
    result = subprocess.run(
        ["bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "openshell-doctor passed all checks." in result.stdout
    assert "1 provider record(s) found; values redacted" in result.stdout
    assert "ghp_SUPER_SECRET_TOKEN_VALUE_12345" not in result.stdout
    assert "ghp_SUPER_SECRET_TOKEN_VALUE_12345" not in result.stderr


def test_openshell_doctor_fails_when_linger_disabled_on_rootless_linux(tmp_path: Path) -> None:
    rendered = _render_template(
        OPENSHELL_DOCTOR_TEMPLATE,
        {
            "chezmoi": {"os": "linux", "username": "mkobit"},
            "local": {"bin": {"openshell": {"installation_method": "github_releases"}}},
        },
        destination=tmp_path,
    )
    assert rendered.returncode == 0, rendered.stderr

    bin_dir = tmp_path / ".local" / "bin"
    bin_dir.mkdir(parents=True)

    _write_executable(
        bin_dir / "openshell",
        "#!/bin/sh\n"
        'case "$1" in\n'
        "  --version) echo 'openshell 0.1.9' ;;\n"
        "  status) exit 0 ;;\n"
        "  gateway) exit 0 ;;\n"
        "  provider) exit 0 ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
    )
    _write_executable(
        bin_dir / "docker",
        "#!/bin/sh\necho 'rootless'\nexit 0\n",
    )
    _write_executable(
        bin_dir / "loginctl",
        "#!/bin/sh\necho 'no'\n",
    )

    env = {**os.environ, "PATH": f"{bin_dir}:/usr/bin:/bin", "USER": "mkobit"}
    result = subprocess.run(
        ["bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    assert result.returncode == 1
    assert "systemd user linger is not enabled" in result.stderr


@pytest.mark.parametrize("override_data", [{}, {"ai": {"sandbox": {"signing_key": "/tmp/old-key"}}}])
def test_sandbox_gitconfig_requires_an_explicit_signing_session(tmp_path: Path, override_data: dict) -> None:
    rendered = _render_template(
        SANDBOX_GITCONFIG_TEMPLATE,
        override_data,
        destination=tmp_path,
    )
    assert rendered.returncode == 0, rendered.stderr
    assert f"path = {tmp_path}/.dotfiles/git/config" in rendered.stdout
    assert "format = ssh" in rendered.stdout
    assert "program = ssh-keygen" in rendered.stdout
    assert "defaultKeyCommand =" in rendered.stdout
    assert "signingkey" not in rendered.stdout
    assert "gpgsign = false" in rendered.stdout
    assert "gpgSign = false" in rendered.stdout
    assert "gpgsign = true" not in rendered.stdout


def test_sandbox_chezmoi_config_disables_host_only_features() -> None:
    with SANDBOX_CHEZMOI_CONFIG.open("rb") as config_file:
        config = tomllib.load(config_file)

    assert config["scriptEnv"] == {
        "MISE_CONFIG_DIR": "/sandbox/.config/mise",
        "MISE_DATA_DIR": "/sandbox/.local/share/mise",
        "MISE_STATE_DIR": "/sandbox/.local/state/mise",
    }
    data = config["data"]
    assert data["zsh"]["set_as_default_login_shell"] is False
    assert data["claude_code"]["installation_method"] == "direct_release"
    assert data["ai"]["plugins"]["superpowers"]["installation_method"] == "chezmoi_external"
    assert data["ai"]["plugins"]["egm"]["installation_method"] == "chezmoi_external"
    assert data["ai"]["plugin_bridge"]["default_hosts"] == ["claude", "codex"]
    assert data["git"]["personal"]["enabled"] is True
    assert data["git_hooks"]["backend"] == "config"
    assert data["git_hooks"]["pre_commit"]["installation_method"] == "none"
    assert data["gemini"]["general"]["enable_auto_update"] is False
    assert data["codex"]["telemetry"]["enabled"] is False
    assert data["local"]["bin"]["agy"] == {
        "installation_method": "github_releases",
        "auto_update": False,
    }
    for host_only_bin in ("openshell", "sbx", "betterleaks"):
        assert data["local"]["bin"][host_only_bin]["installation_method"] == "none"
    for enabled_bin in (
        "codex",
        "mise",
        "gh",
        "ripgrep",
        "fd",
        "jq",
        "bat",
        "delta",
        "fzf",
        "nvim",
        "shellcheck",
        "starship",
        "zoxide",
        "eza",
        "btop",
        "bkt",
        "pi",
    ):
        assert data["local"]["bin"][enabled_bin]["installation_method"] == "github_releases"


def test_sandbox_dockerfile_defines_isolated_sandbox_layer() -> None:
    dockerfile = SANDBOX_DOCKERFILE.read_text(encoding="utf-8")
    base, build_stages = dockerfile.split("\nFROM base AS builder\n", maxsplit=1)
    builder, final = build_stages.split("\nFROM base\n", maxsplit=1)
    assert re.search(r"^FROM debian:bookworm-slim@sha256:[0-9a-f]{64} AS base$", base, re.MULTILINE)
    assert "ARG SANDBOX_UID=1000" in base
    assert "ARG SANDBOX_GID=1000" in base
    assert "HOME=/sandbox" in base
    assert "AGY_CLI_DISABLE_AUTO_UPDATE=true" in base
    assert not re.search(r"^(COPY|ADD)\s", base + builder, re.MULTILINE)
    assert "RUN --mount=type=bind,target=/tmp/dotfiles,readonly " in builder
    assert "--source /tmp/dotfiles" in builder
    assert "--config /tmp/dotfiles/docker/openshell/sandbox-chezmoi.toml" in builder
    assert "--destination /sandbox" in builder
    assert final.splitlines() == [
        "COPY --from=builder /usr/local/bin/chezmoi /usr/local/bin/chezmoi",
        "COPY --from=builder --chown=${SANDBOX_UID}:${SANDBOX_GID} /sandbox /sandbox",
        "WORKDIR /sandbox",
    ]


def test_github_push_policy_limits_access_to_git_transport() -> None:
    policy = yaml.safe_load(GITHUB_PUSH_POLICY.read_text(encoding="utf-8"))
    assert set(policy["filesystem_policy"]["read_write"]) == {"/tmp", "/dev/null"}
    assert "/sandbox" in policy["filesystem_policy"]["read_only"]
    assert policy["landlock"]["compatibility"] == "hard_requirement"

    (network_policy,) = policy["network_policies"].values()
    assert network_policy["binaries"] == [{"path": "/usr/bin/git"}]
    (endpoint,) = network_policy["endpoints"]
    assert endpoint["host"] == "github.com"
    assert endpoint["port"] == 443
    assert endpoint["protocol"] == "rest"
    assert endpoint["enforcement"] == "enforce"
    assert {(rule["allow"]["method"], rule["allow"]["path"]) for rule in endpoint["rules"]} == {
        ("GET", "/mkobit/dotfiles.git/info/refs*"),
        ("POST", "/mkobit/dotfiles.git/git-upload-pack"),
        ("POST", "/mkobit/dotfiles.git/git-receive-pack"),
    }


def test_openshell_skill_and_bootstrap_docs_exist_and_follow_metadata_contract() -> None:
    skill_text = (OPENSHELL_SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(skill_text.split("---", 2)[1])
    assert frontmatter["name"] == "openshell-sandboxes"
    assert "allowed-tools" not in frontmatter
    assert isinstance(frontmatter["description"], str) and frontmatter["description"].strip()
    assert "docs/openshell-bootstrap.md" in skill_text

    openai_meta = yaml.safe_load((OPENSHELL_SKILL_DIR / "exact_agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert openai_meta["interface"]["display_name"] == "OpenShell sandboxes"

    bootstrap_text = OPENSHELL_BOOTSTRAP_DOC.read_text(encoding="utf-8")
    for required in (
        "systemctl --user enable --now openshell-microvm.service",
        "https://docs.nvidia.com/openshell/v0.1.9/tutorials/github-push-access",
        "git fetch",
        "git verify-commit FETCH_HEAD",
    ):
        assert required in bootstrap_text


@pytest.mark.integration
def test_openshell_installed_cli_version(host, chezmoi_data) -> None:
    """Fail when an enabled OpenShell installation is absent or cannot report its version."""
    if installation_method(chezmoi_data, "local.bin.openshell") != "github_releases":
        pytest.skip("local.bin.openshell.installation_method is not 'github_releases'")
    present = host.run("command -v openshell")
    assert present.rc == 0, f"openshell is enabled but absent: {present.stderr}"
    result = host.run("openshell --version")
    assert result.rc == 0, f"openshell --version failed: {result.stderr}"
    version = re.search(r"\bopenshell\s+v?(\d+\.\d+\.\d+)\b", result.stdout)
    assert version is not None, result.stdout
    assert version[1] == chezmoi_data["bin"]["openshell"]["version"]
