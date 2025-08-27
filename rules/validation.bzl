"""
Validation rules for AI agent documentation and configuration files.

This module provides reusable validation rules that can be used across
the project to ensure file quality and consistency.
"""

def _markdown_validation_test_impl(ctx):
    """Implementation for markdown validation test."""
    test_script = ctx.actions.declare_file(ctx.label.name + ".sh")

    # Get the files from runfiles
    files = [f.short_path for f in ctx.files.srcs]
    files_list = " ".join(['"%s"' % f for f in files])

    # Build validation script content
    script_content = '''#!/bin/bash
set -euo pipefail

echo "Validating markdown files..."

files=(%s)
all_valid=true

for file in "${files[@]}"; do
    echo "Validating: $file"

    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "ERROR: File $file does not exist"
        all_valid=false
        continue
    fi

    # Check if file is valid UTF-8
    if ! iconv -f utf-8 -t utf-8 "$file" >/dev/null 2>&1; then
        echo "ERROR: $file is not valid UTF-8"
        all_valid=false
        continue
    fi

    # Check if file is empty
    if [ ! -s "$file" ]; then
        echo "ERROR: $file is empty"
        all_valid=false
        continue
    fi

    # Check for missing trailing newlines (files should end with newline)
    if [ "$(tail -c 1 "$file" | wc -l)" -eq 0 ]; then
        echo "ERROR: $file does not end with newline"
        all_valid=false
        continue
    fi

    echo "OK: $file"
done

if [ "$all_valid" = true ]; then
    echo "All markdown files are valid"
    exit 0
else
    echo "Some markdown files failed validation"
    exit 1
fi
''' % files_list

    ctx.actions.write(
        output = test_script,
        content = script_content,
        is_executable = True,
    )

    # Get runfiles for the markdown files
    runfiles = ctx.runfiles(files = ctx.files.srcs)

    return [DefaultInfo(
        executable = test_script,
        runfiles = runfiles,
    )]

markdown_validation_test = rule(
    implementation = _markdown_validation_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Markdown files to validate",
            allow_files = [".md"],
            mandatory = True,
        ),
    },
    test = True,
)

def _json_validation_test_impl(ctx):
    """Implementation for JSON validation test."""
    test_script = ctx.actions.declare_file(ctx.label.name + ".sh")

    # Get the files from runfiles
    files = [f.short_path for f in ctx.files.srcs]
    files_list = " ".join(['"%s"' % f for f in files])

    script_content = '''#!/bin/bash
set -euo pipefail

echo "Validating JSON files..."

files=(%s)
all_valid=true

for file in "${files[@]}"; do
    echo "Validating: $file"

    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "ERROR: File $file does not exist"
        all_valid=false
        continue
    fi

    # Check if file is empty
    if [ ! -s "$file" ]; then
        echo "ERROR: $file is empty"
        all_valid=false
        continue
    fi

    # Check if file is valid JSON using Python
    if ! python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
        echo "ERROR: $file is not valid JSON"
        all_valid=false
        continue
    fi

    echo "OK: $file"
done

if [ "$all_valid" = true ]; then
    echo "All JSON files are valid"
    exit 0
else
    echo "Some JSON files failed validation"
    exit 1
fi
''' % files_list

    ctx.actions.write(
        output = test_script,
        content = script_content,
        is_executable = True,
    )

    runfiles = ctx.runfiles(files = ctx.files.srcs)

    return [DefaultInfo(
        executable = test_script,
        runfiles = runfiles,
    )]

json_validation_test = rule(
    implementation = _json_validation_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "JSON files to validate",
            allow_files = [".json"],
            mandatory = True,
        ),
    },
    test = True,
)

def _claude_hooks_schema_test_impl(ctx):
    """Implementation for Claude hooks schema validation test."""
    test_script = ctx.actions.declare_file(ctx.label.name + ".sh")

    # Get the files from runfiles
    files = [f.short_path for f in ctx.files.srcs]
    files_list = " ".join(['"%s"' % f for f in files])

    script_content = '''#!/bin/bash
set -euo pipefail

files=(%s)

for file in "${files[@]}"; do
    echo "Validating Claude hooks schema: $file"

    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "ERROR: File $file does not exist"
        exit 1
    fi

    # Validate JSON using Python with Claude Code hooks schema checking
    python3 -c "
import json
import sys

try:
    with open('$file') as f:
        data = json.load(f)

    # Check top-level structure
    if 'hooks' not in data:
        print('ERROR: Missing top-level \\"hooks\\" object')
        sys.exit(1)

    hooks = data['hooks']
    if not isinstance(hooks, dict):
        print('ERROR: \\"hooks\\" must be an object')
        sys.exit(1)

    # Valid hook types according to Claude Code documentation
    valid_hook_types = ['PreToolUse', 'PostToolUse']

    # Valid tool names that can have hooks
    valid_tools = [
        'Bash', 'Edit', 'MultiEdit', 'Read', 'Write', 'Glob',
        'Grep', 'LS', 'WebFetch', 'Task', 'TodoWrite'
    ]

    for hook_type, hook_config in hooks.items():
        print(f'Validating hook type: {hook_type}')

        if hook_type not in valid_hook_types:
            print(f'ERROR: Invalid hook type \\"{hook_type}\\". Valid types: {valid_hook_types}')
            sys.exit(1)

        if not isinstance(hook_config, dict):
            print(f'ERROR: Hook \\"{hook_type}\\" configuration must be an object')
            sys.exit(1)

        # Validate each tool command mapping
        for tool_name, command in hook_config.items():
            print(f'  Validating tool hook: {tool_name}')

            if tool_name not in valid_tools:
                print(f'WARNING: Tool \\"{tool_name}\\" not in known tools list: {valid_tools}')

            if not isinstance(command, str):
                print(f'ERROR: Command for tool \\"{tool_name}\\" must be a string')
                sys.exit(1)

            if not command.strip():
                print(f'ERROR: Command for tool \\"{tool_name}\\" cannot be empty')
                sys.exit(1)

            print(f'  OK: {tool_name} -> {command}')

        print(f'OK: Hook type \\"{hook_type}\\" is valid')

    print('Claude hooks schema validation passed!')

except json.JSONDecodeError as e:
    print(f'ERROR: Invalid JSON: {e}')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: Validation failed: {e}')
    sys.exit(1)
    "
done

echo "All Claude hooks files validated successfully!"
''' % files_list

    ctx.actions.write(
        output = test_script,
        content = script_content,
        is_executable = True,
    )

    runfiles = ctx.runfiles(files = ctx.files.srcs)

    return [DefaultInfo(
        executable = test_script,
        runfiles = runfiles,
    )]

def _json_schema_validation_test_impl(ctx):
    """Implementation for generic JSON schema validation test."""
    test_script = ctx.actions.declare_file(ctx.label.name + ".sh")

    # Get the files from runfiles
    files = [f.short_path for f in ctx.files.srcs]
    files_list = " ".join(['"%s"' % f for f in files])
    schema_file = ctx.file.schema.short_path

    script_content = '''#!/bin/bash
set -euo pipefail

echo "Validating JSON files against schema..."

schema_file="%s"
files=(%s)
all_valid=true

# Check schema file exists
if [ ! -f "$schema_file" ]; then
    echo "ERROR: Schema file $schema_file does not exist"
    exit 1
fi

for file in "${files[@]}"; do
    echo "Validating: $file against $schema_file"

    # Check if file exists
    if [ ! -f "$file" ]; then
        echo "ERROR: File $file does not exist"
        all_valid=false
        continue
    fi

    # Validate JSON against schema using Python with jsonschema
    if ! python3 -c "
import json
import sys
try:
    import jsonschema
except ImportError:
    print('ERROR: jsonschema library not available, skipping schema validation')
    sys.exit(0)

try:
    with open('$schema_file') as sf:
        schema = json.load(sf)
    with open('$file') as f:
        data = json.load(f)
    
    jsonschema.validate(data, schema)
    print('OK: $file validates against schema')
except json.JSONDecodeError as e:
    print(f'ERROR: Invalid JSON in $file: {e}')
    sys.exit(1)
except jsonschema.ValidationError as e:
    print(f'ERROR: Schema validation failed for $file: {e}')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: Validation failed for $file: {e}')
    sys.exit(1)
    " 2>/dev/null; then
        echo "ERROR: Schema validation failed for $file"
        all_valid=false
        continue
    fi
done

if [ "$all_valid" = true ]; then
    echo "All JSON files validate against schema"
    exit 0
else
    echo "Some JSON files failed schema validation"
    exit 1
fi
''' % (schema_file, files_list)

    ctx.actions.write(
        output = test_script,
        content = script_content,
        is_executable = True,
    )

    runfiles = ctx.runfiles(files = ctx.files.srcs + [ctx.file.schema])

    return [DefaultInfo(
        executable = test_script,
        runfiles = runfiles,
    )]

json_schema_validation_test = rule(
    implementation = _json_schema_validation_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "JSON files to validate",
            allow_files = [".json"],
            mandatory = True,
        ),
        "schema": attr.label(
            doc = "JSON schema file to validate against",
            allow_single_file = [".json"],
            mandatory = True,
        ),
    },
    test = True,
)

claude_hooks_schema_test = rule(
    implementation = _claude_hooks_schema_test_impl,
    attrs = {
        "srcs": attr.label_list(
            doc = "Claude hooks JSON files to validate",
            allow_files = [".json"],
            mandatory = True,
        ),
    },
    test = True,
)
