import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
import io

from typing import Any, Dict

# Import the module under test
import src.chezmoi.dot_claude.executable_statusline as statusline

class TestStatusLine(unittest.TestCase):

    def test_format_context_usage(self) -> None:
        # Test low usage (Green)
        self.assertIn(statusline.GREEN, statusline.format_context_usage(10))
        # Test medium usage (Yellow)
        self.assertIn(statusline.YELLOW, statusline.format_context_usage(75))
        # Test high usage (Red)
        self.assertIn(statusline.RED, statusline.format_context_usage(95))
        # Test None (Unknown)
        self.assertIn(statusline.CYAN, statusline.format_context_usage(None))

    def test_format_git_status(self) -> None:
        info: Dict[str, Any] = {
            'branch': 'main',
            'dirty': False,
            'staged': False,
            'ahead': 0,
            'behind': 0,
            'remote': 'https://github.com/example/repo',
            'is_repo': True
        }
        output = statusline.format_git_status(info)
        self.assertIn('main', output)
        self.assertIn(statusline.ICON_CLEAN, output)
        self.assertIn(statusline.ICON_REMOTE, output)

        # Dirty
        info['dirty'] = True
        output = statusline.format_git_status(info)
        self.assertIn(statusline.ICON_DIRTY, output)

        # Staged
        info['dirty'] = False
        info['staged'] = True
        output = statusline.format_git_status(info)
        self.assertIn(statusline.ICON_STAGED, output)

        # Dirty and Staged
        info['dirty'] = True
        info['staged'] = True
        output = statusline.format_git_status(info)
        self.assertIn(statusline.ICON_DIRTY, output)
        self.assertIn(statusline.ICON_STAGED, output)

        # Ahead/Behind
        info['ahead'] = 2
        info['behind'] = 1
        output = statusline.format_git_status(info)
        self.assertIn('↑2', output)
        self.assertIn('↓1', output)

    @patch('subprocess.check_output')
    @patch('os.path.exists')
    def test_get_git_info_fresh(self, mock_exists: MagicMock, mock_check_output: MagicMock) -> None:
        # Mock cache miss
        mock_exists.return_value = False

        # Mock git commands
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd if isinstance(cmd, list) else cmd.split()
            if 'is-inside-work-tree' in cmd_list:
                return b'true'
            if 'rev-parse' in cmd_list and 'HEAD' in cmd_list:
                return "feature-branch\n"
            if 'remote' in cmd_list:
                return "git@github.com:user/repo.git\n"
            if 'status' in cmd_list:
                return " M modified_file.py\n?? untracked.py\n"
            if 'rev-list' in cmd_list:
                return "1\t0\n"
            return ""

        mock_check_output.side_effect = side_effect

        info = statusline.get_git_info('/tmp/repo')

        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual(info['branch'], 'feature-branch')
        self.assertEqual(info['remote'], 'https://github.com/user/repo')
        self.assertTrue(info['dirty'])
        self.assertEqual(info['ahead'], 1)
        self.assertEqual(info['behind'], 0)

    @patch('builtins.print')
    @patch('sys.stdin', new_callable=io.StringIO)
    def test_main(self, mock_stdin: MagicMock, mock_print: MagicMock) -> None:
        # Mock stdin
        input_data = {
            "model": {"display_name": "Claude 3"},
            "workspace": {"current_dir": "/tmp/test"},
            "context_window": {"used_percentage": 50}
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with patch.object(statusline, 'get_git_info') as mock_get_git_info:
            # Mock git info
            mock_get_git_info.return_value = {
                'branch': 'main',
                'dirty': False,
                'staged': False,
                'ahead': 0,
                'behind': 0,
                'remote': None,
                'is_repo': True
            }

            statusline.main()

            # Verify output
            # Expect 2 print calls
            self.assertEqual(mock_print.call_count, 2)

            # Check first line (Model, CWD, Context)
            line1 = mock_print.call_args_list[0][0][0]
            self.assertIn('Claude 3', line1)
            self.assertIn('50%', line1)

            # Check second line (Git)
            line2 = mock_print.call_args_list[1][0][0]
            self.assertIn('main', line2)

if __name__ == '__main__':
    unittest.main()
