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
    
    # Check for trailing newlines
    if [ "$(tail -c 1 "$file" | wc -l)" -gt 0 ]; then
        echo "ERROR: $file ends with trailing newline"
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
    
    # Validate JSON using Python with schema checking
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
    
    # Validate each hook
    valid_on_failure = ['warn', 'block']
    required_fields = ['command', 'description', 'timeout', 'on_failure']
    
    for hook_name, hook_config in hooks.items():
        print(f'Validating hook: {hook_name}')
        
        if not isinstance(hook_config, dict):
            print(f'ERROR: Hook \\"{hook_name}\\" must be an object')
            sys.exit(1)
        
        # Check required fields
        for field in required_fields:
            if field not in hook_config:
                print(f'ERROR: Hook \\"{hook_name}\\" missing required field \\"{field}\\"')
                sys.exit(1)
        
        # Validate field types and values
        if not isinstance(hook_config['command'], str):
            print(f'ERROR: Hook \\"{hook_name}\\" command must be a string')
            sys.exit(1)
        
        if not isinstance(hook_config['description'], str):
            print(f'ERROR: Hook \\"{hook_name}\\" description must be a string')
            sys.exit(1)
        
        if not isinstance(hook_config['timeout'], int) or hook_config['timeout'] <= 0:
            print(f'ERROR: Hook \\"{hook_name}\\" timeout must be a positive integer')
            sys.exit(1)
        
        if hook_config['on_failure'] not in valid_on_failure:
            print(f'ERROR: Hook \\"{hook_name}\\" on_failure must be one of: {valid_on_failure}')
            sys.exit(1)
        
        print(f'OK: Hook \\"{hook_name}\\" is valid')
    
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
