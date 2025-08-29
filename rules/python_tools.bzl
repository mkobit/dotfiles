"""
Python tooling rules for the dotfiles project.

This module provides ruff formatting, linting, and mypy type checking
functionality using hermetic pip dependencies.
"""

def _python_ruff_format_impl(ctx):
    """Implementation for python_ruff_format rule."""
    output_dir = ctx.actions.declare_directory(ctx.label.name + "_formatted")

    # Create a script to run ruff format
    script_content = """#!/bin/bash
set -euo pipefail

RUFF="${{1}}"
OUTPUT_DIR="${{2}}"
shift 2

# Create output directory
mkdir -p "${{OUTPUT_DIR}}"

# Run ruff format on all Python files
for file in "$@"; do
    if [[ "${{file}}" == *.py ]]; then
        relative_path="${{file#$(pwd)/}}"
        output_file="${{OUTPUT_DIR}}/${{relative_path}}"
        output_dir_path="$(dirname "${{output_file}}")"
        
        mkdir -p "${{output_dir_path}}"
        
        # Format the file
        "${{RUFF}}" format --stdin-filename="${{file}}" < "${{file}}" > "${{output_file}}"
    fi
done
"""

    script_file = ctx.actions.declare_file(ctx.label.name + "_format.sh")
    ctx.actions.write(
        output = script_file,
        content = script_content,
        is_executable = True,
    )

    # Get Python files from srcs
    python_files = []
    for src in ctx.attr.srcs:
        for file in src.files.to_list():
            if file.path.endswith(".py"):
                python_files.append(file)

    if python_files:
        args = [ctx.executable._ruff.path, output_dir.path] + [f.path for f in python_files]

        ctx.actions.run(
            outputs = [output_dir],
            inputs = python_files + [ctx.executable._ruff],
            executable = script_file,
            arguments = args,
            mnemonic = "RuffFormat",
            progress_message = "Formatting Python files with ruff %s" % output_dir.short_path,
        )
    else:
        # Create empty output directory if no Python files
        ctx.actions.run_shell(
            outputs = [output_dir],
            command = "mkdir -p {}".format(output_dir.path),
            mnemonic = "RuffFormatEmpty",
            progress_message = "No Python files to format",
        )

    return [DefaultInfo(files = depset([output_dir]))]

def _python_ruff_check_impl(ctx):
    """Implementation for python_ruff_check rule."""

    script_file = ctx.actions.declare_file(ctx.label.name + "_check.sh")

    # Get Python files from srcs
    python_files = []
    for src in ctx.attr.srcs:
        for file in src.files.to_list():
            if file.path.endswith(".py"):
                python_files.append(file)

    if python_files:
        # Create a script to run ruff check
        script_content = """#!/bin/bash
set -euo pipefail

RUFF="${{1}}"
shift 1

echo "Running ruff check on Python files..."
if [[ $# -gt 0 ]]; then
    "${{RUFF}}" check "$@"
    echo "✓ ruff check passed"
else
    echo "No Python files to check"
fi
"""

        ctx.actions.write(
            output = script_file,
            content = script_content,
            is_executable = True,
        )
    else:
        # Create empty test file if no Python files
        ctx.actions.write(
            output = script_file,
            content = "#!/bin/bash\necho 'No Python files to check'\n",
            is_executable = True,
        )

    return [DefaultInfo(
        files = depset([script_file]),
        executable = script_file,
    )]

def _python_mypy_check_impl(ctx):
    """Implementation for python_mypy_check rule."""

    script_file = ctx.actions.declare_file(ctx.label.name + "_mypy.sh")

    # Get Python files from srcs
    python_files = []
    for src in ctx.attr.srcs:
        for file in src.files.to_list():
            if file.path.endswith(".py"):
                python_files.append(file)

    if python_files:
        # Create a script to run mypy
        script_content = """#!/bin/bash
set -euo pipefail

MYPY="${{1}}"
shift 1

echo "Running mypy type checking on Python files..."
if [[ $# -gt 0 ]]; then
    "${{MYPY}}" --ignore-missing-imports "$@"
    echo "✓ mypy type checking passed"
else
    echo "No Python files to check"
fi
"""

        ctx.actions.write(
            output = script_file,
            content = script_content,
            is_executable = True,
        )
    else:
        # Create empty test file if no Python files
        ctx.actions.write(
            output = script_file,
            content = "#!/bin/bash\necho 'No Python files to type check'\n",
            is_executable = True,
        )

    return [DefaultInfo(
        files = depset([script_file]),
        executable = script_file,
    )]

# Rule definitions
python_ruff_format = rule(
    implementation = _python_ruff_format_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to format",
            allow_files = [".py"],
            mandatory = True,
        ),
        "_ruff": attr.label(
            default = "//rules/common:ruff_wrapper",
            executable = True,
            cfg = "exec",
        ),
    },
)

python_ruff_check_test = rule(
    implementation = _python_ruff_check_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to check",
            allow_files = [".py"],
            mandatory = True,
        ),
        "_ruff": attr.label(
            default = "//rules/common:ruff_wrapper",
            executable = True,
            cfg = "exec",
        ),
    },
    test = True,
)

python_mypy_check_test = rule(
    implementation = _python_mypy_check_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to type check",
            allow_files = [".py"],
            mandatory = True,
        ),
        "_mypy": attr.label(
            default = "//rules/common:mypy_wrapper",
            executable = True,
            cfg = "exec",
        ),
    },
    test = True,
)

def python_files_format(name, exclude_patterns = None, **kwargs):
    """Format all Python files in the repository using ruff.

    Args:
        name: Name of the formatting target
        exclude_patterns: List of patterns to exclude from formatting
        **kwargs: Additional attributes passed to python_ruff_format rule
    """
    if exclude_patterns == None:
        exclude_patterns = [
            "bazel-*/**",
        ]

    # Find all Python files
    python_ruff_format(
        name = name,
        srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True),
        **kwargs
    )

def python_files_format_test(name, exclude_patterns = None, **kwargs):
    """Test that all Python files are properly formatted using ruff.

    Args:
        name: Name of the test target
        exclude_patterns: List of patterns to exclude from checking
        **kwargs: Additional attributes passed to python_ruff_check rule
    """
    if exclude_patterns == None:
        exclude_patterns = [
            "bazel-*/**",
        ]

    python_ruff_check_test(
        name = name,
        srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True),
        **kwargs
    )

def python_files_type_check_test(name, exclude_patterns = None, **kwargs):
    """Test that all Python files pass type checking using mypy.

    Args:
        name: Name of the test target
        exclude_patterns: List of patterns to exclude from type checking
        **kwargs: Additional attributes passed to python_mypy_check rule
    """
    if exclude_patterns == None:
        exclude_patterns = [
            "bazel-*/**",
        ]

    python_mypy_check_test(
        name = name,
        srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True),
        **kwargs
    )

def _python_ruff_fix_impl(ctx):
    """Implementation for python_ruff_fix rule that applies auto-fixes."""

    script_file = ctx.actions.declare_file(ctx.label.name + "_fix.sh")

    # Get Python files from srcs
    python_files = []
    for src in ctx.attr.srcs:
        for file in src.files.to_list():
            if file.path.endswith(".py"):
                python_files.append(file)

    if python_files:
        # Create a script to run ruff check --fix
        script_content = """#!/bin/bash
set -euo pipefail

RUFF="${{1}}"
shift 1

echo "Running ruff check --fix on Python files..."
if [[ $# -gt 0 ]]; then
    "${{RUFF}}" check --fix "$@"
    echo "✓ ruff auto-fix completed"
else
    echo "No Python files to fix"
fi
"""

        ctx.actions.write(
            output = script_file,
            content = script_content,
            is_executable = True,
        )
    else:
        # Create empty script if no Python files
        ctx.actions.write(
            output = script_file,
            content = "#!/bin/bash\necho 'No Python files to fix'\n",
            is_executable = True,
        )

    return [DefaultInfo(
        files = depset([script_file]),
        executable = script_file,
    )]

python_ruff_fix = rule(
    implementation = _python_ruff_fix_impl,
    executable = True,
    attrs = {
        "srcs": attr.label_list(
            doc = "Python source files to auto-fix",
            allow_files = [".py"],
            mandatory = True,
        ),
        "_ruff": attr.label(
            default = "//rules/common:ruff_wrapper",
            executable = True,
            cfg = "exec",
        ),
    },
)

def python_files_fix(name, exclude_patterns = None, **kwargs):
    """Auto-fix all Python files in the repository using ruff.

    Args:
        name: Name of the auto-fix target
        exclude_patterns: List of patterns to exclude from fixing
        **kwargs: Additional attributes passed to python_ruff_fix rule
    """
    if exclude_patterns == None:
        exclude_patterns = [
            "bazel-*/**",
        ]

    python_ruff_fix(
        name = name,
        srcs = native.glob(["**/*.py"], exclude = exclude_patterns, allow_empty = True),
        **kwargs
    )
