
with open('pyproject.toml') as f:
    content = f.read()

# Fix the typo if any. Wait, the error is `[project` missing `]`. Let's just restore from git and redo.
