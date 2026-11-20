import pytest
import yaml

def test_dependabot_only_assigns_repository_owner(pytestconfig: pytest.Config) -> None:
    config = yaml.safe_load((pytestconfig.rootpath / ".github/dependabot.yml").read_text(encoding="utf-8"))
    for update in config["updates"]:
        assert "reviewers" not in update
        assert set(update.get("assignees", [])) <= {"mkobit"}
