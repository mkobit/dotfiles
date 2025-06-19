#!/bin/bash
set -euo pipefail

# Configuration - will be replaced by Bazel
TARGET_FILE="__TARGET_FILE__"
IDENTIFIER="__IDENTIFIER__"
HEADER_COMMENT="__HEADER_COMMENT__"
INCLUDE_DIRECTIVE="__INCLUDE_DIRECTIVE__"
LABEL="__LABEL__"
CONFIG_FILE_PATH="__CONFIG_FILE_PATH__"
BACKUP="__BACKUP__"
CREATE_IF_MISSING="__CREATE_IF_MISSING__"

# Expand tilde in target file path
if [[ "$TARGET_FILE" == "~/"* ]]; then
    TARGET_FILE_EXPANDED="$HOME/${TARGET_FILE#"~/"}"
else
    TARGET_FILE_EXPANDED="$TARGET_FILE"
fi

echo "Include installation operation"
echo "Target file: $TARGET_FILE_EXPANDED"
echo "Identifier: $IDENTIFIER"

# Function to find the actual config file path
find_config_file() {
    local config_path="$1"

    # Try multiple paths to find the config file
    local script_path="$0"
    local runfiles_dir="${script_path}.runfiles/_main"

    local possible_paths=(
        "$config_path"                           # Direct path from Bazel
        "$runfiles_dir/$config_path"            # In runfiles directory
        "$(dirname "$script_path")/../$config_path"  # Relative to script directory
        "$PWD/$config_path"                     # Relative to current directory
    )

    for path in "${possible_paths[@]}"; do
        if [[ -f "$path" ]]; then
            echo "$path"
            return 0
        fi
    done

    echo "Error: Config file not found: $config_path" >&2
    return 1
}

# Find the actual config file and get its absolute path
FOUND_CONFIG_FILE=$(find_config_file "$CONFIG_FILE_PATH")
if [[ -z "$FOUND_CONFIG_FILE" ]]; then
    exit 1
fi

# Convert to relative path using bazel-bin symlink if possible
CONFIG_ABSOLUTE_PATH=$(realpath "$FOUND_CONFIG_FILE")
echo "Found config file at: $CONFIG_ABSOLUTE_PATH"

# Try to create a relative path using bazel-bin
# Find the original workspace by looking for bazel-bin symlink from the target file location
TARGET_DIR="$(dirname "$TARGET_FILE_EXPANDED")"
WORKSPACE_ROOT=""

# Search upwards from target directory to find workspace root
SEARCH_DIR="$TARGET_DIR"
while [[ "$SEARCH_DIR" != "/" ]]; do
    if [[ -L "$SEARCH_DIR/bazel-bin" ]]; then
        WORKSPACE_ROOT="$SEARCH_DIR"
        break
    fi
    SEARCH_DIR="$(dirname "$SEARCH_DIR")"
done

# If we couldn't find workspace from target dir, try common locations
if [[ -z "$WORKSPACE_ROOT" ]]; then
    for potential_workspace in "$HOME/dotfiles" "$HOME/workspace" "$PWD"; do
        if [[ -L "$potential_workspace/bazel-bin" ]]; then
            WORKSPACE_ROOT="$potential_workspace"
            break
        fi
    done
fi

if [[ -n "$WORKSPACE_ROOT" ]] && [[ "$CONFIG_ABSOLUTE_PATH" == *"/bazel-out/"* ]]; then
    # Extract the path after bazel-out/.../bin/ and create bazel-bin path
    BAZEL_OUT_SUFFIX="${CONFIG_ABSOLUTE_PATH#*bazel-out/}"
    # Skip the architecture/config part and get the path after bin/
    BIN_SUFFIX="${BAZEL_OUT_SUFFIX#*/bin/}"
    BAZEL_BIN_PATH="$WORKSPACE_ROOT/bazel-bin/$BIN_SUFFIX"
    echo "Trying bazel-bin path: $BAZEL_BIN_PATH"
    if [[ -f "$BAZEL_BIN_PATH" ]]; then
        CONFIG_INCLUDE_PATH="$BAZEL_BIN_PATH"
        echo "Using bazel-bin path: $CONFIG_INCLUDE_PATH"
    else
        CONFIG_INCLUDE_PATH="$CONFIG_ABSOLUTE_PATH"
        echo "bazel-bin path not found, using absolute path: $CONFIG_INCLUDE_PATH"
    fi
else
    CONFIG_INCLUDE_PATH="$CONFIG_ABSOLUTE_PATH"
    echo "Not a bazel-out path or workspace not found, using absolute path: $CONFIG_INCLUDE_PATH"
fi

# Check if target file exists
if [[ ! -f "$TARGET_FILE_EXPANDED" ]]; then
    if [[ "$CREATE_IF_MISSING" == "true" ]]; then
        echo "Target file doesn't exist, creating new file..."
        TARGET_DIR="$(dirname "$TARGET_FILE_EXPANDED")"
        if [[ ! -d "$TARGET_DIR" ]]; then
            echo "Creating directory: $TARGET_DIR"
            mkdir -p "$TARGET_DIR"
        fi
        touch "$TARGET_FILE_EXPANDED"
    else
        echo "Error: Target file doesn't exist and create_if_missing is false: $TARGET_FILE_EXPANDED"
        exit 1
    fi
fi

# Create backup if requested
if [[ "$BACKUP" == "true" ]]; then
    BACKUP_FILE="${TARGET_FILE_EXPANDED}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Creating backup: $BACKUP_FILE"
    cp "$TARGET_FILE_EXPANDED" "$BACKUP_FILE"
fi

# Create temp file for safe operation
TEMP_FILE="$(mktemp)"
trap 'rm -f "$TEMP_FILE"' EXIT

# Guard identifiers
GUARD_BEGIN="$HEADER_COMMENT guard:begin:$IDENTIFIER"
GUARD_END="$HEADER_COMMENT guard:end:$IDENTIFIER"



# Function to check if include section exists
include_exists() {
    local file="$1"
    local guard_begin="$2"

    grep -Fq "$guard_begin" "$file" 2>/dev/null
}

# Function to get include section bounds
get_include_bounds() {
    local file="$1"
    local guard_begin="$2"
    local guard_end="$3"

    local begin_num=$(grep -Fn "$guard_begin" "$file" | head -1 | cut -d: -f1)
    if [[ -z "$begin_num" ]]; then
        echo "0 0"
        return
    fi

    local end_num=$(grep -Fn "$guard_end" "$file" | head -1 | cut -d: -f1)
    if [[ -z "$end_num" ]]; then
        echo "0 0"
        return
    fi

    echo "$begin_num $end_num"
}

# Create the include directive content by substituting {path}
INCLUDE_CONTENT="${INCLUDE_DIRECTIVE//\{path\}/$CONFIG_INCLUDE_PATH}"

# Main installation logic
if include_exists "$TARGET_FILE_EXPANDED" "$GUARD_BEGIN"; then
    echo "Include section '$IDENTIFIER' exists, updating..."

    # Get section boundaries
    read -r begin_num end_num <<< "$(get_include_bounds "$TARGET_FILE_EXPANDED" "$GUARD_BEGIN" "$GUARD_END")"

    if [[ $begin_num -eq 0 ]]; then
        echo "Error: Could not find include section boundaries for '$IDENTIFIER'"
        exit 1
    fi

    echo "Include section found at lines $begin_num-$end_num"

    # Extract content before the section
    if [[ $begin_num -gt 1 ]]; then
        head -n $((begin_num - 1)) "$TARGET_FILE_EXPANDED" > "$TEMP_FILE"
    else
        > "$TEMP_FILE"
    fi

    # Add the updated include section
    echo "$GUARD_BEGIN" >> "$TEMP_FILE"
    echo "$INCLUDE_CONTENT" >> "$TEMP_FILE"
    echo "$GUARD_END" >> "$TEMP_FILE"

    # Extract content after the section
    total_lines=$(wc -l < "$TARGET_FILE_EXPANDED")
    if [[ $end_num -lt $total_lines ]]; then
        tail -n +$((end_num + 1)) "$TARGET_FILE_EXPANDED" >> "$TEMP_FILE"
    fi

    echo "Updated existing include section '$IDENTIFIER'"

else
    echo "Include section '$IDENTIFIER' doesn't exist, adding new section..."

    # Copy existing content
    cp "$TARGET_FILE_EXPANDED" "$TEMP_FILE"

    # Add blank line if file doesn't end with one
    if [[ -s "$TEMP_FILE" ]] && [[ "$(tail -c1 "$TEMP_FILE" | wc -l)" -eq 0 ]]; then
        echo "" >> "$TEMP_FILE"
    fi

    # Add the new include section
    echo "$GUARD_BEGIN" >> "$TEMP_FILE"
    echo "$INCLUDE_CONTENT" >> "$TEMP_FILE"
    echo "$GUARD_END" >> "$TEMP_FILE"

    echo "Added new include section '$IDENTIFIER'"
fi

# Atomically replace the target file
mv "$TEMP_FILE" "$TARGET_FILE_EXPANDED"
echo "Successfully installed include directive for '$IDENTIFIER' to: $TARGET_FILE_EXPANDED"
