import pytest
import yaml

from bin_updater.pr_summary import update_title


def test_dependabot_only_assigns_repository_owner(pytestconfig: pytest.Config) -> None:
    config = yaml.safe_load((pytestconfig.rootpath / ".github/dependabot.yml").read_text(encoding="utf-8"))
    for update in config["updates"]:
        assert "reviewers" not in update
        assert set(update.get("assignees", [])) <= {"mkobit"}


def test_dependabot_and_binary_updates_use_the_same_title_prefix(pytestconfig: pytest.Config) -> None:
    config = yaml.safe_load((pytestconfig.rootpath / ".github/dependabot.yml").read_text(encoding="utf-8"))
    for update in config["updates"]:
        commit_message = update["commit-message"]
        assert commit_message["include"] == "scope"
        assert update_title("example", "1.0", "2.0").startswith(f"{commit_message['prefix']}(deps): ")
