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

| Command | Purpose |
|---|---|
| `uv run ruff check .` | Lint |
| `uv run ruff format --check .` | Format |
| `uv run ty check` | Type check |
| `uv run pytest src/python` | Tests |

## Coding guidelines

Prefer functional, immutable, and non-imperative code.
Avoid mutability and reassignment wherever possible.
Code should be declarative and heavily lean on Python's built-in functional capabilities.

### Test asyncio
When writing async tests, prefer using `pytest-asyncio` and decorating your test functions with `@pytest.mark.asyncio` rather than using `unittest.IsolatedAsyncioTestCase`.

### Module separation
Do not put types or models in central `types.py` or `models.py` files.
Instead, namespace types and models into their corresponding canonical domain locations.


### Avoid `list.append()` and mutation

Do not initialize empty lists and conditionally append or `extend` to them.
Instead, use list comprehensions, generators, or build a sequence and filter it.

❌ **Bad:**
```python
results = []
if condition_a:
    results.append("a")
if condition_b:
    results.append("b")
```

✅ **Good:**
```python
items = [
    "a" if condition_a else None,
    "b" if condition_b else None,
]
results = [item for item in items if item is not None]

def get_results() -> Iterator[str]:
    if condition_a:
        yield "a"
    if condition_b:
        yield "b"
```

### Use immutable types for parameters

Prefer `typing.Sequence`, `typing.Iterable`, `typing.Mapping`, and other immutable/read-only types over mutable ones like `list`.

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

### Avoid variable reassignment and string concatenation

Treat variables as `const`.
Do not reassign a variable once it is defined.
For strings, avoid using `+=` or iterative concatenation.

❌ **Bad:**
```python
message = "Hello"
if condition:
    message += ", User"
else:
    message += ", Guest"
```

✅ **Good:**
```python
name = "User" if condition else "Guest"
message = f"Hello, {name}"

parts = ["Hello", ", User" if condition else ", Guest"]
message = "".join(parts)
```

### Anti-pattern: imperative list deduplication
Avoid using mutable sets and `list.append()` inside loops for deduplication.
**Anti-pattern:**
```python
seen = set()
ordered = []
for item in reversed(items):
    if item not in seen:
        seen.add(item)
        ordered.append(item)
```
**Preferred:**
```python
ordered = list(dict.fromkeys(reversed(items)))
```
