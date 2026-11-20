"""Verify OpenCode configuration follows the host and plugin control plane."""

import asyncio
import json
import shutil
from pathlib import Path

import pytest
from integration_support.chezmoi import chezmoi_argv, run_chezmoi

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"


@pytest.mark.parametrize("ignore_layer", ["base", "overlay"])
async def test_opencode_apply_respects_host_and_plugin_control_plane(tmp_path, ignore_layer):
    ignore_source = SOURCE_ROOT
    if ignore_layer == "overlay":
        ignore_source = SOURCE_ROOT.parents[3] / "src/chezmoi"
        if not (ignore_source / ".chezmoiignore.tmpl").is_file():
            pytest.skip("the overlay ignore policy is not available in this checkout")
    source = tmp_path / "source"
    for relative in (
        ".chezmoiignore.tmpl",
        ".chezmoidata/ai/plugins/superpowers.toml",
        "dot_config/opencode/modify_opencode.json",
        ".chezmoitemplates/ai/plugin-ignore",
        ".chezmoitemplates/ai/authored-plugins",
    ):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2((ignore_source if relative == ".chezmoiignore.tmpl" else SOURCE_ROOT) / relative, target)

    async def apply_case(case_dir, host_method, plugin_method, seed, expected):
        destination = case_dir / "destination"
        destination.mkdir(parents=True)
        config = case_dir / "chezmoi.json"
        target = destination / ".config/opencode/opencode.json"
        package = str(
            destination / ".local/share/agent-plugins/marketplaces/superpowers-marketplace/plugins/superpowers"
        )
        legacy = str(destination / ".local/share/agent-plugins/marketplace/plugins/superpowers")
        foreign = {"plugin": ["custom-plugin"], "model": "custom/model"}
        paths = {"foreign": [], "managed": [package], "legacy": [legacy], "both": [legacy, package]}

        def settings(kind):
            return {**foreign, "plugin": [*foreign["plugin"], *paths[kind]]}

        initial = None
        if seed is not None:
            initial = json.dumps(settings(seed), indent=2) + "\n"
            target.parent.mkdir(parents=True)
            target.write_text(initial)

        data = {
            "ai": {"plugins": {"superpowers": {"installation_method": plugin_method}}},
            "local": {"bin": {"opencode": {} if host_method is None else {"installation_method": host_method}}},
            "mise": {},
        }
        config.write_text(json.dumps({"data": data}))
        async with slots:
            result = await run_chezmoi(
                chezmoi_argv(
                    "apply",
                    source=source,
                    config=config,
                    destination=destination,
                    cache=case_dir / "cache",
                    state=case_dir / "state.boltdb",
                )
            )

        assert result.returncode == 0, (case_dir.name, result.stderr)
        if expected is None:
            assert not target.exists(), case_dir.name
        elif expected == "unchanged":
            assert target.read_text() == initial, case_dir.name
        else:
            assert json.loads(target.read_text()) == settings(expected), case_dir.name

    cases = [
        (f"{method or 'unset'}-{seed or 'absent'}", method, "chezmoi_external", seed, "unchanged" if seed else None)
        for method in (None, "none")
        for seed in (None, "managed", "legacy")
    ] + [
        ("add-plugin", "preinstalled", "chezmoi_external", "foreign", "managed"),
        ("replace-legacy", "preinstalled", "chezmoi_external", "legacy", "managed"),
        ("remove-duplicate", "preinstalled", "chezmoi_external", "both", "managed"),
        ("remove-managed", "preinstalled", "none", "managed", "foreign"),
        ("remove-legacy", "preinstalled", "none", "legacy", "foreign"),
    ]
    slots = asyncio.Semaphore(3)
    async with asyncio.TaskGroup() as group:
        for name, host_method, plugin_method, seed, expected in cases:
            group.create_task(apply_case(tmp_path / name, host_method, plugin_method, seed, expected))
