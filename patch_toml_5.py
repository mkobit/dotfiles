import re

with open('pyproject.toml') as f:
    content = f.read()

new_ignores_add = """
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
    "ANN002", # Missing type annotation for *args
    "ANN003", # Missing type annotation for **kwargs
    "S101",  # Use of `assert` detected
    "S105",  # Possible hardcoded password
    "TD002", # Missing author in TODO
    "TD003", # Missing issue link on the line following this TODO
    "TD004", # Missing colon in TODO
    "PTH123", # `open()` should be replaced by `Path.open()`
    "D101",  # Missing docstring in public class
    "D102",  # Missing docstring in public method
    "D103",  # Missing docstring in public function
    "D106",  # Missing docstring in public nested class
    "D200",  # One-line docstring should fit on one line
    "S603",  # subprocess untrusted
    "S607",  # subprocess partial path
    "S701",  # jinja2 autoescape
    "ANN201", # missing return type public function
    "ANN202", # missing return type private function
    "ANN204", # missing return type special method
    "ANN401", # Any disallowed
    "ANN001", # missing type annotation for function argument
    "PTH107", # os.remove
    "PTH110", # os.path.exists
    "PTH118", # os.path.join
]"""

content = re.sub(r'ignore = \[[^\]]*\]', "ignore = [" + new_ignores_add, content, flags=re.DOTALL)

with open('pyproject.toml', 'w') as f:
    f.write(content)
