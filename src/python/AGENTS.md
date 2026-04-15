# Python tools (uv workspace)

## Creating a new tool

1. **Create Python package**: `mkdir -p src/python/my_tool`
   - `src/python/my_tool/main.py`: Entry point.
   - `src/python/my_tool/pyproject.toml`:
     ```toml
     [project]
     name = "my-tool"
     version = "0.0.0"
     requires-python = ">=3.14"
     dependencies = ["click>=8"]

     [project.scripts]
     my-tool = "my_tool.main:cli"

     [build-system]
     requires = ["hatchling"]
     build-backend = "hatchling.build"
     ```

2. **Register in workspace**: Add to `members` in the root `pyproject.toml`:
   ```toml
   [tool.uv.workspace]
   members = [
       "src/python/my_tool",
       ...
   ]
   ```

3. **Create chezmoi executable template**: `src/chezmoi/dot_local/bin/tools/executable_my_tool.tmpl`
   ```toml
   {{- if eq .local_bin_tools.my_tool.installation "uv" -}}
   #!/bin/bash
   exec uv run --project {{ .chezmoi.sourceDir }}/src/python/my_tool -m my_tool.main "$@"
   {{- end -}}
   ```

4. **Add chezmoi data**: In `src/chezmoi/.chezmoidata/local_bin_tools.toml`:
   ```toml
   [local_bin_tools.my_tool]
   installation = "uv"
   ```

5. **Deploy**: `chezmoi apply ~/.local/bin/tools/my_tool`

## Module imports

Use the package name directly (not the full workspace path):
- ✅ `from my_tool.lib import ...`
- ❌ `from src.python.my_tool.lib import ...`

## Quality tools

Run from the workspace root:
- `uv run ruff check .` — lint
- `uv run ruff format --check .` — format
- `uv run ty check src/python` — type check
- `uv run pytest src/python` — tests

## Coding Guidelines

We prefer **functional, immutable, and non-imperative code**. Avoid mutability and reassignment wherever possible. Code should be clean, declarative, and heavily lean on Python's built-in functional capabilities.

### 1. Avoid `list.append()` and Mutation
Do not initialize empty lists and conditionally append to them. Instead, use list comprehensions, generators, or build a sequence and filter it.

❌ **Bad (Imperative & Mutating):**
```python
results = []
if condition_a:
    results.append("a")
if condition_b:
    results.append("b")
```

✅ **Good (Functional & Declarative):**
```python
# Option 1: List comprehension / filter
items = [
    "a" if condition_a else None,
    "b" if condition_b else None,
]
results = [item for item in items if item is not None]

# Option 2: Yielding (Generators)
def get_results() -> Iterator[str]:
    if condition_a:
        yield "a"
    if condition_b:
        yield "b"
```

### 2. Use Immutable Types for Parameters
Instead of passing mutable `list` types around (which could accidentally be modified), prefer passing `typing.Sequence` or `typing.Iterable`.

❌ **Bad:**
```python
def process_data(items: list[str]) -> list[str]:
    ...
```

✅ **Good:**
```python
from collections.abc import Sequence, Iterable

def process_data(items: Sequence[str]) -> Sequence[str]:
    ...
```

### 3. Avoid Variable Reassignment & String Concatenation
Treat variables as `const` (like in TypeScript). Do not reassign a variable once it is defined. For strings, avoid using `+=` or iterative concatenation.

❌ **Bad (String Concatenation & Reassignment):**
```python
message = "Hello"
if condition:
    message += ", User"
else:
    message += ", Guest"
```

✅ **Good (Assignment once via functional style):**
```python
name = "User" if condition else "Guest"
message = f"Hello, {name}"
# OR using join for lists of strings
parts = ["Hello", ", User" if condition else ", Guest"]
message = "".join(parts)
```
