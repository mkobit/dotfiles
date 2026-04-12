with open('src/python/claude_statusline/tests/test_main.py', 'r') as f:
    content = f.read()

import re

# Replace actual newlines within the string literals with \n
content = re.sub(r'stdout = "feature-branch\n"', r'stdout = "feature-branch\\n"', content)
content = re.sub(r'stdout = "git@github.com:user/repo.git\n"', r'stdout = "git@github.com:user/repo.git\\n"', content)
content = re.sub(r'stdout = " M modified_file.py\n\?\? untracked.py\n"', r'stdout = " M modified_file.py\\n?? untracked.py\\n"', content)
content = re.sub(r'stdout = "1\t0\n"', r'stdout = "1\\t0\\n"', content)
content = re.sub(r'stdout = "true\n"', r'stdout = "true\\n"', content)

with open('src/python/claude_statusline/tests/test_main.py', 'w') as f:
    f.write(content)
