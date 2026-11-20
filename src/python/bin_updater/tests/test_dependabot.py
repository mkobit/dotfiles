from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]


def test_dependabot_does_not_notify_assignees_or_reviewers() -> None:
    config = yaml.safe_load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"))
    for update in config["updates"]:
        unexpected = {"assignees", "reviewers"} & update.keys()
        assert not unexpected, (update["package-ecosystem"], unexpected)
