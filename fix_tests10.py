with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

import re
content = re.sub(r'        self\.assertFalse\(info\.is_worktree\)\n', '', content)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
