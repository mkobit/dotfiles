import re

with open('pyproject.toml') as f:
    content = f.read()

new_select = """select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
    "N",   # pep8-naming
    "C90", # mccabe
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
    "RET", # flake8-return
    "PIE", # flake8-pie
    "ISC", # flake8-implicit-str-concat
    "RUF", # Ruff-specific rules
    "PL",  # Pylint
    "PERF", # Perflint
    "TID", # flake8-tidy-imports
    "PYI", # flake8-pyi
    "ARG", # flake8-unused-arguments
    "PTH", # flake8-use-pathlib
    "TD",  # flake8-todos
    "S",   # flake8-bandit
    "ANN", # flake8-annotations
    "D",   # pydocstyle
]"""

new_ignore = """ignore = [
    "UP043", # Unnecessary default type arguments
    "PLR2004", # Magic value used in comparison
    "PLR0912", # Too many branches
    "PLR0913", # Too many arguments
    "PLR0915", # Too many statements
    "D100",  # Missing docstring in public module
    "D104",  # Missing docstring in public package
    "D105",  # Missing docstring in magic method
    "D107",  # Missing docstring in __init__
    "D203",  # 1 blank line required before class docstring
    "D212",  # Multi-line docstring summary should start at the first line
    "ANN101", # Missing type annotation for `self` in method
    "ANN102", # Missing type annotation for `cls` in classmethod
    "ANN002", # Missing type annotation for *args
    "ANN003", # Missing type annotation for **kwargs
    "S101",  # Use of `assert` detected
    "S105",  # Possible hardcoded password
    "TD002", # Missing author in TODO
    "TD003", # Missing issue link on the line following this TODO
    "TD004", # Missing colon in TODO
    "PTH123", # `open()` should be replaced by `Path.open()`
]"""

pydocstyle_config = """
[tool.ruff.lint.pydocstyle]
convention = "google"
"""

content = re.sub(r'select = \[[^\]]*\]', new_select, content, flags=re.DOTALL)
content = re.sub(r'ignore = \[[^\]]*\]', new_ignore, content, flags=re.DOTALL)

if "tool.ruff.lint.pydocstyle" not in content:
    content += pydocstyle_config

with open('pyproject.toml', 'w') as f:
    f.write(content)
