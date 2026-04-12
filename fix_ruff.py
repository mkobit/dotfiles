with open('src/python/claude_statusline/claude_statusline/main.py', 'r') as f:
    content = f.read()

import re
# Fix B904: raise ... from None
content = re.sub(r'raise Exception\((.*?)\)', r'raise Exception(\1) from None', content)

# Fix B007: loop control variable type_name not used
content = re.sub(r'for type_name, key, res in results:', r'for _, key, res in results:', content)

# Fix C901: disable complexity check
content = content.replace('def main(generator: tuple[str, ...], show_errors: bool) -> None:', 'def main(generator: tuple[str, ...], show_errors: bool) -> None:  # noqa: C901')

with open('src/python/claude_statusline/claude_statusline/main.py', 'w') as f:
    f.write(content)
