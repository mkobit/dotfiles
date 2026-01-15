# Python CLI tools build and deployment

## Overview

Python CLI tools are built with Bazel and deployed to the destination directory (typically `~/.local/bin/tools/`) via chezmoi using a wrapper script that invokes `bazel run`.

**Workflow:**
1. `chezmoi apply` generates a wrapper script in the destination directory (typically `~/.local/bin/tools/`) for the tool.
2. The wrapper script executes `bazel run //src/python/my_tool:my_tool`.
3. Bazel builds and runs the tool on demand (or uses cached build).

## Creating a new tool

### 1. Create Python package

```bash
mkdir -p src/python/my_tool
```

Add `src/python/my_tool/main.py` and `src/python/my_tool/BUILD.bazel`:

```starlark
load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "my_tool",
    srcs = ["main.py"],
    deps = [requirement("click")],
)
```

### 2. Create chezmoi executable template

Add `src/chezmoi/dot_local/bin/tools/executable_my_tool.tmpl`:

```toml
{{- template "bazel_run_wrapper.sh" (dict "chezmoi" .chezmoi "target" "//src/python/my_tool:my_tool") -}}
```

### 3. Deploy

```bash
chezmoi apply ~/.local/bin/tools/my_tool
~/.local/bin/tools/my_tool --help
```

## Adding dependencies

Add to `requirements.in` (unpinned):
```
click
pydantic
```

Update Bazel requirements:
```bash
bazel run //:requirements.update
bazel run //:gazelle_python_manifest.update
```

## Troubleshooting

**Import errors:**
Use full module paths: `from src.python.my_tool.lib import ...`

## Example

See `src/python/hello_world/` for complete example with Click CLI, Pydantic models, and tests.
