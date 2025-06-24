"""
Simple guarded installation rule for dotfiles.
"""

def guarded_install_rule(
        name,
        target_file,
        guard_prefix,
        guard_id,
        srcs,
        content,
        **kwargs):
    """Creates a simple guarded install rule.

    Args:
        name: Name of the rule
        target_file: Path to install to (e.g., "~/.vimrc")
        guard_prefix: Comment character (e.g., "\"", "#")
        guard_id: Identifier for the section (e.g., "dotfiles:vimrc")
        srcs: Source files to reference in content
        content: Template string for content generation
        **kwargs: Additional arguments
    """

    # Create the install script
    script_name = name + "_install.sh"

    # Simple template-based content generation
    native.genrule(
        name = name + "_script",
        srcs = srcs,
        outs = [script_name],
        cmd = '''
cat > $@ << 'EOF'
#!/bin/bash
set -euo pipefail

TARGET_FILE="{target_file}"
GUARD_PREFIX='{guard_prefix}'
GUARD_ID="{guard_id}"
GUARD_START="$$GUARD_PREFIX BEGIN $$GUARD_ID"
GUARD_END="$$GUARD_PREFIX END $$GUARD_ID"

# Expand tilde
if [[ "$$TARGET_FILE" == "~/"* ]]; then
    TARGET_FILE="$$HOME/$${{TARGET_FILE:2}}"
fi

# Content to insert
CONTENT='{content}'

# Create directory if needed
mkdir -p "$$(dirname "$$TARGET_FILE")"

# Create temp file
TEMP_FILE="$$(mktemp)"
trap 'rm -f "$$TEMP_FILE"' EXIT

if [[ -f "$$TARGET_FILE" ]]; then
    # Look for existing section
    if grep -Fq "$$GUARD_START" "$$TARGET_FILE"; then
        echo "Updating existing section..."
        # Remove old section and add new one
        sed "/$$GUARD_START/,/$$GUARD_END/d" "$$TARGET_FILE" > "$$TEMP_FILE"
    else
        echo "Adding new section..."
        cp "$$TARGET_FILE" "$$TEMP_FILE"
        echo "" >> "$$TEMP_FILE"
    fi
else
    echo "Creating new file..."
    touch "$$TEMP_FILE"
fi

# Add our section
echo "$$GUARD_START" >> "$$TEMP_FILE"
echo "$$CONTENT" >> "$$TEMP_FILE"
echo "$$GUARD_END" >> "$$TEMP_FILE"

# Install atomically
mv "$$TEMP_FILE" "$$TARGET_FILE"
echo "Installed to $$TARGET_FILE"
EOF

chmod +x $@
        '''.format(
            target_file = target_file,
            guard_prefix = guard_prefix.replace("'", "\\'"),
            guard_id = guard_id,
            content = content.replace("'", "\\'"),
        ),
    )

    # Create executable
    native.sh_binary(
        name = name,
        srcs = [script_name],
        **kwargs
    )

# Export the rule
guarded_install = guarded_install_rule


