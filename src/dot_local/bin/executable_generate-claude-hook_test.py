import json
import subprocess
import unittest
from rules_python.python.runfiles import runfiles

class TestGenerateClaudeHook(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment by locating the script to test using runfiles.
        """
        r = runfiles.Create()
        self.script_path = r.Rlocation("__main__/src/dot_local/bin/generate-claude-hook")

    def test_basic_hook_generation(self):
        """
        Tests the basic generation of a hook configuration.
        """
        command = [
            self.script_path,
            "--event", "PreToolUse",
            "--matcher", "Bash",
            "--command", "echo 'Hello from hook'"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        output_json = json.loads(result.stdout)

        expected_json = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'Hello from hook'"
                            }
                        ]
                    }
                ]
            }
        }

        self.assertEqual(output_json, expected_json)

    def test_pipe_separated_matcher(self):
        """
        Tests the hook generation with a pipe-separated matcher.
        """
        command = [
            self.script_path,
            "--event", "PostToolUse",
            "--matcher", "Edit|Write",
            "--command", "npx prettier --write $FILE_PATH"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        output_json = json.loads(result.stdout)

        expected_json = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "npx prettier --write $FILE_PATH"
                            }
                        ]
                    }
                ]
            }
        }

        self.assertEqual(output_json, expected_json)

    def test_wildcard_matcher(self):
        """
        Tests the hook generation with a wildcard matcher.
        """
        command = [
            self.script_path,
            "--event", "PreToolUse",
            "--matcher", "*",
            "--command", "echo 'All tools hook'"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        output_json = json.loads(result.stdout)

        expected_json = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "*",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo 'All tools hook'"
                            }
                        ]
                    }
                ]
            }
        }

        self.assertEqual(output_json, expected_json)

    def test_invalid_event_type(self):
        """
        Tests that the script fails when an invalid event type is provided.
        """
        command = [
            self.script_path,
            "--event", "InvalidEventType",
            "--matcher", "Bash",
            "--command", "echo 'This should not run'"
        ]
        # We expect this to fail, so we don't use check=True
        result = subprocess.run(command, capture_output=True, text=True)

        # Assert that the script exited with a non-zero status code
        self.assertNotEqual(result.returncode, 0)

        # Assert that the stderr contains the expected error message from argparse
        self.assertIn("invalid choice: 'InvalidEventType'", result.stderr)

if __name__ == "__main__":
    unittest.main()
