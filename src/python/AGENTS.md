# Python CLI tools build and deployment

## Creating a new tool

1. **Create Python package**: `mkdir -p src/python/my_tool`
   - `src/python/my_tool/main.py`: Entry point.
   - `src/python/my_tool/BUILD.bazel`:
     ```starlark
     load("@pypi//:requirements.bzl", "requirement")
     load("@rules_python//python:defs.bzl", "py_binary")

     py_binary(
         name = "my_tool",
         srcs = ["main.py"],
         deps = [requirement("click")],
     )
     ```

2. **Create chezmoi executable template**: `src/chezmoi/dot_local/bin/tools/executable_my_tool.tmpl`
   ```toml
   {{- template "bazel_run_wrapper.sh" (dict "chezmoi" .chezmoi "target" "//src/python/my_tool:my_tool") -}}
   ```

3. **Deploy**: `chezmoi apply ~/.local/bin/tools/my_tool`

## Import Troubleshooting

- **Import errors**: Use full module paths rooted at `src.python`:
  - ✅ `from src.python.my_tool.lib import ...`
  - ❌ `from .lib import ...`
