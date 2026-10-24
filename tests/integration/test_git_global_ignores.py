import json
import shutil
import subprocess

import pytest


@pytest.mark.parametrize("ignores", [None, [], ["zebra/", "*.swp", ".worktrees/"], ["*.log", "!important.log"]])
def test_git_global_ignores_apply(tmp_path, chezmoi_source_root, ignores):
    relative = "dot_dotfiles/git/snippets/gitignore_global.tmpl"
    source = tmp_path / "source"
    template = source / relative
    template.parent.mkdir(parents=True)
    shutil.copyfile(chezmoi_source_root / relative, template)
    dest = tmp_path / "dest"
    target = dest / ".dotfiles/git/snippets/gitignore_global"
    target.parent.mkdir(parents=True)
    target.write_text("stale-pattern\n")
    config = tmp_path / "chezmoi.json"
    data = {} if ignores is None else {"git": {"global_ignores": ignores}}
    config.write_text(json.dumps({"data": data}))
    command = [
        "chezmoi",
        "--source",
        str(source),
        "--destination",
        str(dest),
        "--config",
        str(config),
        "--persistent-state",
        str(tmp_path / "state.boltdb"),
        "--cache",
        str(tmp_path / "cache"),
        "--no-tty",
    ]

    subprocess.run([*command, "apply", "--force"], capture_output=True, text=True, check=True)

    if ignores:
        assert target.read_text().splitlines() == [
            "# Global .gitignore file",
            "# Documentation: https://git-scm.com/docs/gitignore",
            *ignores,
        ]
    else:
        assert not target.exists()
