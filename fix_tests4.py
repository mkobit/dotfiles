import re

with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

# I see the problem. git mock is returning `GitInfo(...)` still!
content = content.replace(
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            mock_get_git_info.return_value = GitInfo(
                branch="main",
                dirty=False,
                staged=False,
                untracked=False,
                ahead=0,
                behind=0,
                remote=None,
                is_repo=True,
                is_worktree=False,
            )""",
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            mock_get_git_info.return_value = []"""
)

content = content.replace(
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            mock_get_git_info.return_value = GitInfo(
                branch="feature-branch",
                dirty=True,
                staged=False,
                untracked=False,
                ahead=0,
                behind=0,
                remote=None,
                is_repo=True,
                is_worktree=True,
            )""",
"""        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            mock_get_git_info.return_value = []"""
)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
