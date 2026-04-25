
with open('pyproject.toml') as f:
    content = f.read()

# Replace the TQM that is not a real rule with TD (flake8-todos) as per user's list: "TQM", # flake8-todo
# And fix some other missing things in per-file-ignores.

per_file_ignores = """
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "ANN", "ARG", "S", "PTH"]
"src/**/tests/**/*.py" = ["D", "ANN", "ARG", "S", "PTH"]
"src/**/conftest.py" = ["D", "ANN", "ARG", "S", "PTH"]
"""

if "tool.ruff.lint.per-file-ignores" not in content:
    content += per_file_ignores

with open('pyproject.toml', 'w') as f:
    f.write(content)
