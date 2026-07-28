# Python tools (uv workspace)

## Creating a new tool

A new tool needs three registrations, or it won't build or deploy.
Copy an existing package (e.g. `sandboxr/`) as a template for the shape.

1. `src/python/<name>/` package with `main.py` and a `pyproject.toml` declaring `[project.scripts]`.
2. Added to `members` under `[tool.uv.workspace]` in the root `pyproject.toml`.
3. A catalog entry in `src/chezmoi/.chezmoidata/local_bin_tools.toml` (`source_dir`, `package_name`), and an `installation_method = "dotfiles.uv"` entry in `.chezmoi.toml.tmpl` under `[data.local_bin_tools.<name>]`.
   The catalog entry alone is inert — `chezmoi apply` only installs tools opted in via the second file.

The executable name comes from `[project.scripts]`.
It lands at `{{ .chezmoi.destDir }}/.local/bin/dotfiles/<name>` via the `run_onchange` install script.

## Renaming or retiring a tool

Keep the old catalog key.
Set `installation_method = "uninstall"` with its `package_name` so the `run_onchange` script's uninstall branch removes the stale uv tool and bin symlink.
Delete the key only after all machines have applied.

## Module imports

Import via the package name (`from my_tool.lib import ...`), not the workspace path (`from src.python.my_tool.lib import ...`).

## Module organization

Don't centralize types or models into `types.py` or `models.py`.
Namespace them into their owning domain module instead.

## Quality tools

| Command | Purpose |
|---|---|
| `uv run ruff check .` | Lint |
| `uv run ruff format --check .` | Format |
| `uv run ty check` | Type check |
| `uv run pytest src/python` | Tests |

Scope pytest to `src/python`.
Unscoped, it also collects the top-level `tests/integration/` suite, which asserts against local machine state.

Use `pytest-asyncio` (`@pytest.mark.asyncio`) for async tests, not `unittest.IsolatedAsyncioTestCase`.

## Coding style

Prefer functional, declarative code: comprehensions and generators over manual accumulation, `Sequence`/`Iterable`/`Mapping` over `list` for read-only parameters.
Match the surrounding code's idiom rather than forcing this where an imperative form is genuinely clearer.
See [functional-style.md](functional-style.md) for the patterns and anti-patterns.
