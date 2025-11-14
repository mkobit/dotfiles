import unittest
from executable_generate-claude-hook import generate_hook_config

class TestGenerateClaudeHook(unittest.TestCase):

    def test_basic_hook_generation(self):
        """
        Tests the basic generation of a hook configuration.
        """
        result = generate_hook_config(
            event="PreToolUse",
            matcher_str="Bash",
            command="echo 'Hello from hook'"
        )

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

        self.assertDictEqual(result, expected_json)

    def test_pipe_separated_matcher(self):
        """
        Tests the hook generation with a pipe-separated matcher.
        """
        result = generate_hook_config(
            event="PostToolUse",
            matcher_str="Edit|Write",
            command="npx prettier --write $FILE_PATH"
        )

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

        self.assertDictEqual(result, expected_json)

    def test_wildcard_matcher(self):
        """
        Tests the hook generation with a wildcard matcher.
        """
        result = generate_hook_config(
            event="PreToolUse",
            matcher_str="*",
            command="echo 'All tools hook'"
        )

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

        self.assertDictEqual(result, expected_json)

if __name__ == "__main__":
    unittest.main()
