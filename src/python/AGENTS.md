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
