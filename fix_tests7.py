with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

# _run_git_cmd now uses asyncio.create_subprocess_exec instead of subprocess.run, so we need to mock that instead of subprocess.run in test_get_git_info_fresh.

content = content.replace(
    '@patch("subprocess.run")',
    '@patch("asyncio.create_subprocess_exec")'
)

# the side_effect for asyncio.create_subprocess_exec needs to return a mock process that has a communicate method returning (stdout, stderr) and returncode 0.

mock_side_effect = """        async def mock_communicate():
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
            return stdout.encode(), b""

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = mock_communicate
        return mock_proc"""

# We need to replace the side_effect function in test_get_git_info_fresh
import re

content = re.sub(
    r'def side_effect\(cmd: Any, \*\*kwargs: Any\) -> Any:.*?return mock_res',
    """async def side_effect(*cmd: Any, **kwargs: Any) -> Any:
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
        return mock_proc""",
    content,
    flags=re.DOTALL
)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
