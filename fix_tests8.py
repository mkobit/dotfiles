with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

import re

# In the previous python script, \\n got interpreted as a literal newline during regex replacement. Let's fix that.
# Let's just rewrite the test directly using a literal string.

new_test_func = '''    @patch("asyncio.create_subprocess_exec")
    def test_get_git_info_fresh(self, mock_run: MagicMock) -> None:
        async def side_effect(*cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd
            stdout = ""
            if "rev-parse" in cmd_list and "HEAD" in cmd_list:
                stdout = "feature-branch\\n"
            elif "ls-remote" in cmd_list:
                stdout = "git@github.com:user/repo.git\\n"
            elif "status" in cmd_list:
                stdout = " M modified_file.py\\n?? untracked.py\\n"
            elif "rev-list" in cmd_list:
                stdout = "1\\t0\\n"
            elif "rev-parse" in cmd_list and "--is-inside-work-tree" in cmd_list:
                stdout = "true\\n"

            async def mock_communicate():
                return stdout.encode(), b""

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = mock_communicate
            return mock_proc

        mock_run.side_effect = side_effect

        with patch.object(Path, "exists", return_value=False):
            with patch("claude_statusline.segments.git._check_is_repo", return_value=True):
                import asyncio; from claude_statusline.segments.git import generate_git_segment; info = asyncio.run(generate_git_segment(Path("/tmp/repo"), False))

        self.assertTrue(len(info) > 0)
        assert info is not None
        self.assertTrue("feature-branch" in info[0].segment.text)'''

content = re.sub(
    r'    @patch\("asyncio\.create_subprocess_exec"\)\n    def test_get_git_info_fresh.*?self\.assertTrue\("feature-branch" in info\[0\]\.segment\.text\)',
    new_test_func,
    content,
    flags=re.DOTALL
)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
