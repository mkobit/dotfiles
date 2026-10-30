import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from termstatus.segments.workspace import format_obsidian_vault


class TestFormatObsidianVault(unittest.TestCase):
    def test_obsidian_vault_found_in_ancestor(self) -> None:
        with TemporaryDirectory() as tmpdir:
            vault_dir = Path(tmpdir) / "my_vault"
            obsidian_dir = vault_dir / ".obsidian"
            obsidian_dir.mkdir(parents=True)
            sub_dir = vault_dir / "notes" / "daily"
            sub_dir.mkdir(parents=True)

            res = format_obsidian_vault(sub_dir)
            self.assertEqual(len(res), 1)
            self.assertIn("my_vault", res[0].segment.text)

    def test_obsidian_vault_not_found(self) -> None:
        with TemporaryDirectory() as tmpdir:
            res = format_obsidian_vault(Path(tmpdir))
            self.assertEqual(res, [])


if __name__ == "__main__":
    unittest.main()
