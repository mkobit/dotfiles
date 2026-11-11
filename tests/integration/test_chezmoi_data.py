import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from chezmoi_test_data import (
    AGY_INSTALLATION_METHODS,
    MARKER_GATED_INSTALLATION_METHODS,
    installation_method,
    required_installation_method,
)


@pytest.mark.parametrize("github_actions", ["true", "false", ""])
def test_ghostty_installation_matches_runner_environment(tmp_path, github_actions):
    expected = "none" if github_actions == "true" else "homebrew" if sys.platform == "darwin" else "snap"
    template = Path.cwd() / "src/chezmoi/.chezmoi.toml.tmpl"
    source = tmp_path / "source"
    source.mkdir()
    (source / ".chezmoi.toml.tmpl").write_text(template.read_text())
    config = tmp_path / "chezmoi.toml"
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            str(config),
            "--config-format",
            "toml",
            "--source",
            str(source),
            "--destination",
            str(tmp_path / "dest"),
            "--cache",
            str(tmp_path / "cache"),
            "--persistent-state",
            str(tmp_path / "state.db"),
            "init",
            "--no-tty",
        ],
        env={**os.environ, "CI": "true", "GITHUB_ACTIONS": github_actions},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    data = tomllib.loads(config.read_text())["data"]
    assert required_installation_method(data, "packages.ghostty") == expected


def test_installation_method_reads_top_level_feature():
    data = {"local": {"bin": {"agy": {"installation_method": "preinstalled"}}}}

    assert installation_method(data, "local.bin.agy") == "preinstalled"


def test_installation_method_reads_dotted_feature_path():
    data = {"packages": {"strace": {"installation_method": "apt"}}}

    assert installation_method(data, "packages.strace") == "apt"


def test_required_installation_method_reads_dotted_feature_path():
    data = {"packages": {"strace": {"installation_method": "apt"}}}

    assert required_installation_method(data, "packages.strace") == "apt"


def test_installation_method_defaults_missing_dotted_path_to_none():
    data = {"packages": {}}

    assert installation_method(data, "packages.strace") == "none"


def test_required_installation_method_rejects_missing_dotted_path():
    data = {"packages": {}}

    with pytest.raises(KeyError, match=r"packages\.strace"):
        required_installation_method(data, "packages.strace")


def test_installation_method_defaults_missing_feature_to_none():
    assert installation_method({}, "local.bin.agy") == "none"


def test_installation_method_defaults_missing_method_to_none():
    assert installation_method({"local": {"bin": {"agy": {}}}}, "local.bin.agy") == "none"


def test_required_installation_method_rejects_missing_method():
    with pytest.raises(KeyError, match=r"local\.bin\.agy\.installation_method"):
        required_installation_method({"local": {"bin": {"agy": {}}}}, "local.bin.agy")


def test_required_installation_method_rejects_non_string_method():
    with pytest.raises(TypeError, match=r"local\.bin\.agy\.installation_method"):
        required_installation_method({"local": {"bin": {"agy": {"installation_method": []}}}}, "local.bin.agy")


@pytest.mark.integration
def test_chezmoi_data_contains_agy_installation_method(chezmoi_data):
    assert "local" in chezmoi_data and "bin" in chezmoi_data["local"] and "agy" in chezmoi_data["local"]["bin"]
    assert installation_method(chezmoi_data, "local.bin.agy") in AGY_INSTALLATION_METHODS


@pytest.mark.integration
@pytest.mark.parametrize("feature,methods", MARKER_GATED_INSTALLATION_METHODS.items())
def test_marker_gated_installation_method_contract(chezmoi_data, feature, methods):
    assert required_installation_method(chezmoi_data, feature) in methods


@pytest.mark.integration
def test_chezmoi_data_contains_git_global_ignores_including_worktrees(chezmoi_data):
    assert "git" in chezmoi_data and "global_ignores" in chezmoi_data["git"]
    assert ".worktrees/" in chezmoi_data["git"]["global_ignores"]
    assert ".worktree/" in chezmoi_data["git"]["global_ignores"]
