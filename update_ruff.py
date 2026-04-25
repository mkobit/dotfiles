
import tomli
import tomli_w

with open("pyproject.toml", "rb") as f:
    config = tomli.load(f)

lint = config["tool"]["ruff"]["lint"]
select = lint.get("select", [])

# User's requested additions (mapped TQM to TD)
to_add = ["ARG", "PTH", "TD", "S", "ANN", "D"]
for item in to_add:
    if item not in select:
        select.append(item)

lint["select"] = select

# Add ignores to avoid hampering productivity
ignore = lint.get("ignore", [])
new_ignores = [
    "D100", # Missing docstring in public module
    "D104", # Missing docstring in public package
    "D105", # Missing docstring in magic method
    "D107", # Missing docstring in __init__
    "ANN101", # Missing type annotation for `self` in method
    "ANN102", # Missing type annotation for `cls` in classmethod
    "S101", # Use of `assert` detected (often used in tests and simple scripts)
    "TD002", # Missing author in TODO
    "TD003", # Missing issue link on the line following this TODO
]
for item in new_ignores:
    if item not in ignore:
        ignore.append(item)

lint["ignore"] = ignore

# Setup per-file-ignores for tests to be less strict
pfi = lint.get("per-file-ignores", {})
test_patterns = ["tests/**/*.py", "src/**/tests/**/*.py", "src/**/conftest.py"]
for pattern in test_patterns:
    if pattern not in pfi:
        pfi[pattern] = []
    for rule in ["D", "ANN", "ARG", "S", "PTH"]:
        if rule not in pfi[pattern]:
            pfi[pattern].append(rule)

lint["per-file-ignores"] = pfi

# Fix docstyle convention to avoid conflicts
if "pydocstyle" not in lint:
    lint["pydocstyle"] = {"convention": "google"}

with open("pyproject.toml", "wb") as f:
    tomli_w.dump(config, f)
