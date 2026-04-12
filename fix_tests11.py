with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

import re

# Fix imports and formatting for the single-line statement
old_stmt = 'import asyncio; from claude_statusline.segments.git import generate_git_segment; info = asyncio.run(generate_git_segment(Path("/tmp/repo"), False))'
new_stmt = '''import asyncio
                from claude_statusline.segments.git import generate_git_segment
                info = asyncio.run(generate_git_segment(Path("/tmp/repo"), False))'''

content = content.replace(old_stmt, new_stmt)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
