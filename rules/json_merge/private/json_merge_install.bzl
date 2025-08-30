"""
JSON merge with guarded installation support.

Combines JSON merging with the existing guarded install pattern for safe
deployment to home directory files.
"""

load("//rules/common:guarded_install.bzl", "guarded_install")
load("//rules/json_merge/private:json_merge.bzl", "json_merge")

def json_merge_install(
        name,
        srcs,
        target_file,
        merge_document = None,
        guard_prefix = "#",
        guard_id = None,
        strategy = "deep_merge",
        **kwargs):
    """
    Merge JSON files and install with guarded installation.
    
    This macro combines JSON merging with guarded installation, allowing
    safe deployment of merged JSON configurations to target files.
    
    Args:
        name: Name of the installation target
        srcs: JSON files to merge (in order of precedence)
        target_file: Target file path (e.g., "~/.config/app/config.json")
        merge_document: Optional JSON merge document
        guard_prefix: Comment character for guards (default: "#")
        guard_id: Guard identifier (defaults to name)
        strategy: Merge strategy (default: "deep_merge")
        **kwargs: Additional arguments passed to guarded_install
    """
    
    if not guard_id:
        guard_id = "dotfiles:json_merge:%s" % name
    
    # Create merged JSON file
    merged_file = name + "_merged.json"
    json_merge(
        name = name + "_merge",
        srcs = srcs,
        merge_document = merge_document,
        out = merged_file,
        strategy = strategy,
    )
    
    # Generate installation script that merges JSON with existing file
    install_script_name = name + "_install.sh"
    
    native.genrule(
        name = name + "_install_script",
        srcs = [":" + name + "_merge"],
        outs = [install_script_name],
        executable = True,
        cmd = '''
cat > $@ << 'EOF'
#!/bin/bash
set -euo pipefail

TARGET_FILE="{target_file}"
GUARD_PREFIX='{guard_prefix}'
GUARD_ID="{guard_id}"
GUARD_START="$$GUARD_PREFIX dotfiles/json_merge:BEGIN:$$GUARD_ID"
GUARD_END="$$GUARD_PREFIX dotfiles/json_merge:END:$$GUARD_ID"
MERGED_JSON="$(cat $(location :{merge_target}))"

# Expand tilde
if [[ "$$TARGET_FILE" == "~/"* ]]; then
    TARGET_FILE="$$HOME/$${{TARGET_FILE:2}}"
fi

# Create directory if needed
mkdir -p "$$(dirname "$$TARGET_FILE")"

# Create temp file
TEMP_FILE="$$(mktemp)"
trap 'rm -f "$$TEMP_FILE"' EXIT

if [[ -f "$$TARGET_FILE" ]]; then
    # Check if target is JSON
    if ! python3 -c "import json; json.load(open('$$TARGET_FILE'))" 2>/dev/null; then
        echo "Warning: Target file $$TARGET_FILE is not valid JSON, using guarded text insertion"
        
        # Fall back to text-based guarded install
        if grep -Fq "$$GUARD_START" "$$TARGET_FILE"; then
            echo "Updating existing JSON section..."
            ESCAPED_START="$$(echo "$$GUARD_START" | sed 's/\\//\\\\\\//g')"
            ESCAPED_END="$$(echo "$$GUARD_END" | sed 's/\\//\\\\\\//g')"
            sed "/$$ESCAPED_START/,/$$ESCAPED_END/d" "$$TARGET_FILE" > "$$TEMP_FILE"
        else
            echo "Adding new JSON section..."
            cp "$$TARGET_FILE" "$$TEMP_FILE"
            echo "" >> "$$TEMP_FILE"
        fi
        
        # Add our JSON section as text
        echo "$$GUARD_START" >> "$$TEMP_FILE"
        echo "$$MERGED_JSON" >> "$$TEMP_FILE"
        echo "$$GUARD_END" >> "$$TEMP_FILE"
    else
        echo "Merging with existing JSON file..."
        # Merge JSON files properly
        python3 -c "
import json
import sys

try:
    # Load existing JSON
    with open('$$TARGET_FILE', 'r') as f:
        existing = json.load(f)
    
    # Load our merged JSON
    merged = json.loads('''$$MERGED_JSON''')
    
    # Perform deep merge
    def deep_merge(base, update):
        if isinstance(base, dict) and isinstance(update, dict):
            result = base.copy()
            for key, value in update.items():
                if key in result:
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        elif isinstance(base, list) and isinstance(update, list):
            return base + update
        else:
            return update
    
    result = deep_merge(existing, merged)
    
    # Write merged result
    with open('$$TEMP_FILE', 'w') as f:
        json.dump(result, f, indent=2, sort_keys=True, separators=(',', ': '))
        f.write('\\n')
        
    print('Successfully merged JSON files')
    
except Exception as e:
    print(f'Error merging JSON: {{e}}', file=sys.stderr)
    sys.exit(1)
        "
    fi
else
    echo "Creating new JSON file..."
    echo "$$MERGED_JSON" > "$$TEMP_FILE"
fi

# Install atomically
mv "$$TEMP_FILE" "$$TARGET_FILE"
echo "Installed merged JSON to $$TARGET_FILE"
EOF

chmod +x $@
        '''.format(
            target_file = target_file,
            guard_prefix = guard_prefix.replace("'", "\\'"),
            guard_id = guard_id,
            merge_target = name + "_merge",
        ),
    )
    
    # Create executable install target
    native.sh_binary(
        name = name,
        srcs = [install_script_name],
        data = [":" + name + "_merge"],
        tags = ["manual"],  # Prevent accidental execution
        **kwargs
    )