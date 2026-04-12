import re

with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

# Fix mock patches for _check_is_repo
content = content.replace(
    'patch("claude_statusline.main._check_is_repo", return_value=True)',
    'patch("claude_statusline.segments.git._check_is_repo", return_value=True)'
)

# Replace patch of get_git_info with generate_git_segment
content = content.replace(
    'patch.object(main_module, "get_git_info")',
    'patch("claude_statusline.main.generate_git_segment")'
)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
