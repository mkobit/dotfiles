import json
import subprocess
import sys

from skill_filter import plugin_bridge


def test_migrate_ownership_writes_canonical_tsv(tmp_path):
    legacy = tmp_path / "ownership.json"
    legacy.write_text(
        json.dumps(
            {
                "resources": [
                    {"kind": "plugin", "host": "claude", "id": "demo@market"},
                    {"kind": "marketplace", "host": "codex", "id": "market"},
                ]
            }
        )
    )

    result = subprocess.run(
        [sys.executable, str(plugin_bridge.__file__), "migrate-ownership", str(legacy)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        result.stdout == "plugin\tclaude\tmarket\tdemo\nmarketplace\tcodex\tmarket\t\n"
    )


def test_has_identity_accepts_exact_json_identity():
    result = subprocess.run(
        [
            sys.executable,
            str(plugin_bridge.__file__),
            "has-identity",
            "--field",
            "id",
            "--expected",
            "demo@market",
        ],
        input='[{"id":"demo@market"}]\n',
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    result = subprocess.run(
        [
            sys.executable,
            str(plugin_bridge.__file__),
            "has-identity",
            "--field",
            "id",
            "--expected",
            "demo@market",
        ],
        input='[{"id":"demographic@market"}]\n',
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
