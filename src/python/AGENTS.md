# Python CLI tools build and deployment

## Overview

Python CLI tools are built with Bazel into standalone zipapp executables and deployed to `~/.local/bin/tools/` via chezmoi.

**Workflow:**
1. `chezmoi apply` runs hook: `bazel build //...`
2. Bazel creates zipapp executables in `bazel-bin/`
3. Chezmoi queries Bazel for artifact paths and copies to `~/.local/bin/tools/`

## Creating a new tool

### 1. Create Python package

```bash
mkdir -p src/python/my_tool
```

Add `src/python/my_tool/main.py` and `src/python/my_tool/BUILD.bazel`:

```starlark
load("@pypi//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")
load("//tools/python/private:zipapp.bzl", "python_zipapp")

py_binary(
    name = "my_tool",
    srcs = ["main.py"],
    deps = [requirement("click")],
)

python_zipapp(
    name = "my_tool_exe",
    binary = ":my_tool",
    visibility = ["//visibility:public"],
)
```

### 2. Create chezmoi external

Add `src/chezmoi/dot_local/bin/tools/.chezmoiexternals/my_tool.toml.tmpl`:

```toml
{{- includeTemplate "dotfiles_bazel_python_tool.toml" (dict "target" "//src/python/my_tool:my_tool_exe" "name" "my_tool") -}}
```

### 3. Deploy

```bash
chezmoi apply ~/.local/bin/tools/my_tool
~/.local/bin/tools/my_tool --help
```

## Bazel rules

### `python_zipapp` rule

**Location:** `//tools/python/private:zipapp.bzl`

Creates a standalone executable zipapp by prepending `#!/usr/bin/env python3` shebang to a py_binary .zip file.

**Attributes:**
- `binary` (label, required): py_binary target. Must be built with `--build_python_zip` flag (configured in `.bazelrc`).

**Returns:**
Executable file with runfiles support for data dependencies.

**Implementation:**
1. Finds `.zip` file in py_binary outputs
2. Prepends shebang: `printf "#!/usr/bin/env python3\n" > "$1" && cat "$2" >> "$1"`
3. Fails with error if `.zip` not found (check `.bazelrc` has `build --build_python_zip`)

**Platform support:** macOS, Linux (uses shell, not Windows compatible)

**Example:**
```starlark
python_zipapp(
    name = "my_tool_exe",
    binary = ":my_tool",
    visibility = ["//visibility:public"],
)
```

### `python_cli_tool` macro

**Location:** `//tools/python:defs.bzl`

Convenience macro that generates py_binary, python_zipapp, and py_test targets.

**Parameters:**
- `name` (string): Base name for generated targets
- `main` (string): Entry point Python file
- `srcs` (list): Additional source files
- `deps` (list): Dependencies (use `requirement("pkg")` for pip)
- `data` (list): Data files
- `test_srcs` (list): Test source files
- `test_deps` (list): Additional test dependencies
- `visibility` (list): Visibility specification
- `tags` (list): Tags applied to all targets

**Generated targets:**
- `{name}`: py_binary for `bazel run`
- `{name}_exe`: zipapp executable
- `{name}_test`: py_test (only if test_srcs provided)

**Example:**
```starlark
load("//tools/python:defs.bzl", "python_cli_tool")

python_cli_tool(
    name = "my_tool",
    main = "main.py",
    srcs = ["lib.py"],
    deps = [requirement("click")],
    test_srcs = ["test_lib.py"],
)
```

## Chezmoi template reference

### `dotfiles_bazel_python_tool.toml` template

**Location:** `.chezmoitemplates/dotfiles_bazel_python_tool.toml`

Reusable template for creating chezmoi externals for Bazel-built Python tools.

**Parameters:**
- `target` (string): Bazel target label (e.g., `"//src/python/hello_world:hello_world_exe"`)
- `name` (string): Install name (e.g., `"hello_world"`)

**How it works:**
- Queries `bazel cquery --output=files` for artifact path
- Queries `bazel info workspace` for repository root
- Combines into absolute path for chezmoi external
- Works across all build configurations (debug/opt, arm64/amd64)

**Usage:**
```toml
{{- includeTemplate "dotfiles_bazel_python_tool.toml" (dict "target" "//src/python/my_tool:my_tool_exe" "name" "my_tool") -}}
```

## Adding dependencies

Add to `requirements.txt`:
```
click==8.1.7
pydantic==2.9.2
```

Update Bazel:
```bash
bazel run //:gazelle_python_manifest.update
```

## Troubleshooting

**"No .zip output found":**
Verify `build --build_python_zip` exists in `.bazelrc`

**Tool not deploying:**
Test template: `chezmoi execute-template < src/chezmoi/dot_local/bin/tools/.chezmoiexternals/my_tool.toml.tmpl`

**Import errors:**
Use full module paths: `from src.python.my_tool.lib import ...`

## Example

See `src/python/hello_world/` for complete example with Click CLI, Pydantic models, and tests.
