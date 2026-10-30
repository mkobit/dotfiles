from pathlib import Path

from termstatus.segments.workspace import format_directory, format_obsidian_vault


class TestFormatDirectory:
    def test_format_directory(self, tmp_path: Path):
        results = format_directory(tmp_path)
        assert len(results) == 2
        assert results[0].generator == "internal.workspace"
        assert results[1].generator == "internal.workspace"
        assert str(tmp_path) in results[1].segment.text


class TestFormatObsidianVault:
    def test_obsidian_vault_found_in_ancestor(self, tmp_path: Path):
        vault_dir = tmp_path / "my_vault"
        obsidian_dir = vault_dir / ".obsidian"
        obsidian_dir.mkdir(parents=True)
        sub_dir = vault_dir / "notes" / "daily"
        sub_dir.mkdir(parents=True)

        results = format_obsidian_vault(sub_dir)
        assert len(results) == 1
        assert "my_vault" in results[0].segment.text

    def test_obsidian_vault_not_found(self, tmp_path: Path):
        results = format_obsidian_vault(tmp_path)
        assert results == []
