from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]


def test_dependabot_only_assigns_repository_owner() -> None:
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
    for update in config["updates"]:
        assert "reviewers" not in update
        assert set(update.get("assignees", [])) <= {"mkobit"}
