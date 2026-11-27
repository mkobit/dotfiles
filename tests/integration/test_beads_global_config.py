import json
import shutil

import pytest

from chezmoi_cli import ChezmoiCli


def _beads_config(tmp_path, chezmoi_source_root):
    template = chezmoi_source_root / "dot_config/bd/private_config.yaml.tmpl"
    assert template.is_file(), "Beads global config template is missing"
    source = tmp_path / "source"
    source_template = source / "dot_config/bd/private_config.yaml.tmpl"
    source_template.parent.mkdir(parents=True)
    shutil.copyfile(template, source_template)
    dest = tmp_path / "dest"
    target = dest / ".config/bd/config.yaml"
    target.parent.mkdir(parents=True)
    config = tmp_path / "chezmoi.json"
    cli = ChezmoiCli(
        source=source,
        destination=dest,
        config=config,
        persistent_state=tmp_path / "state.boltdb",
        cache=tmp_path / "cache",
        no_tty=True,
    )
    return config, target, cli


@pytest.mark.parametrize("data", [{}, {"beads": {"global": {"config": {}}}}])
def test_beads_global_config_empty_deletes_existing_file(tmp_path, chezmoi_source_root, data):
    config, target, cli = _beads_config(tmp_path, chezmoi_source_root)
    config.write_text(json.dumps({"data": data}))
    target.write_text("unmanaged: stale\n")

    diff = cli.diff(target).run(check=True)
    assert "-unmanaged: stale" in diff.stdout
    cli.apply(target, force=True).run(check=True)

    assert not target.exists()


def test_beads_global_config_applies_arbitrary_overlay_keys(tmp_path, chezmoi_source_root):
    config, target, cli = _beads_config(tmp_path, chezmoi_source_root)
    config.write_text(
        json.dumps(
            {
                "data": {
                    "beads": {
                        "global": {
                            "config": {
                                "zebra": {"z": 2, "a": 1},
                                "no-git-ops": False,
                                "dolt": {"auto-push": True, "auto-commit": "on"},
                                "array": [{"z": 2, "a": 1}, "last", "first"],
                            }
                        }
                    }
                }
            }
        )
    )
    target.write_text("stale: true\n")

    diff = cli.diff(target).run(check=True)
    assert "-stale: true" in diff.stdout
    cli.apply(target, force=True).run(check=True)

    assert target.stat().st_mode & 0o777 == 0o600
    assert target.read_text() == (
        'array:\n- a: 1\n  z: 2\n- last\n- first\ndolt:\n  auto-commit: "on"\n  auto-push: true\n'
        "no-git-ops: false\nzebra:\n  a: 1\n  z: 2\n"
    )
    diff = cli.diff(target).run(check=True)
    assert diff.stdout == ""
