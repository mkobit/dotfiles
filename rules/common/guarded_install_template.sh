#!/bin/bash
set -euo pipefail

# Configuration - will be replaced by Bazel
TARGET_FILE="__TARGET_FILE__"
HEADER_COMMENT="__HEADER_COMMENT__"
GUARD_START="__GUARD_START__"
GUARD_END="__GUARD_END__"
LABEL="__LABEL__"
CONTENT_FILE="__CONTENT_FILE__"

# Expand tilde in target file path
if [[ "$TARGET_FILE" == "~/"* ]]; then
    TARGET_FILE_EXPANDED="$HOME/${TARGET_FILE#"~/"}"
else
    TARGET_FILE_EXPANDED="$TARGET_FILE"
fi

echo "Installing dotfiles content to: $TARGET_FILE_EXPANDED"
echo "Label: $LABEL"

# Read content from our source file
# Try multiple paths to find the content file, including Bazel runfiles
SCRIPT_PATH="$0"
SCRIPT_NAME="$(basename "$SCRIPT_PATH")"
RUNFILES_DIR="${SCRIPT_PATH}.runfiles/_main"

# Extract the target path from the CONTENT_FILE (remove bazel-out prefix if present)
CONTENT_TARGET_PATH="$CONTENT_FILE"
if [[ "$CONTENT_FILE" == bazel-out/* ]]; then
    # Extract the actual target path from bazel-out path
    # Format: bazel-out/darwin_arm64-fastbuild/bin/src/git/gitconfig.gitconfig -> src/git/gitconfig.gitconfig
    CONTENT_TARGET_PATH="${CONTENT_FILE#*/bin/}"
fi

POSSIBLE_PATHS=(
    "$CONTENT_FILE"                                    # Direct path from Bazel
    "$RUNFILES_DIR/$CONTENT_FILE"                     # In runfiles directory with full path
    "$RUNFILES_DIR/$CONTENT_TARGET_PATH"              # In runfiles directory with target path
    "$(dirname "$SCRIPT_PATH")/../$CONTENT_FILE"      # Relative to script directory
    "$PWD/$CONTENT_FILE"                              # Relative to current directory
    "$PWD/$(basename "$CONTENT_FILE")"                # Just the filename in current dir
)

FOUND_CONTENT_FILE=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if [[ -f "$path" ]]; then
        FOUND_CONTENT_FILE="$path"
        echo "Found content file at: $FOUND_CONTENT_FILE"
        break
    fi
done

if [[ -z "$FOUND_CONTENT_FILE" ]]; then
    echo "Content file not found. Tried paths:"
    for path in "${POSSIBLE_PATHS[@]}"; do
        echo "  $path"
    done
    exit 1
fi

CONTENT="$(cat "$FOUND_CONTENT_FILE")"

# Create directory if it doesn't exist
TARGET_DIR="$(dirname "$TARGET_FILE_EXPANDED")"
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Creating directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

# Create temp file for safe operation
TEMP_FILE="$(mktemp)"
trap 'rm -f "$TEMP_FILE"' EXIT

# Check if target file exists
if [[ -f "$TARGET_FILE_EXPANDED" ]]; then
    echo "Target file exists, checking for existing managed section..."

    # Check if our managed section already exists
    HEADER_LINE="$HEADER_COMMENT dotfiles installed $LABEL"
    START_GUARD_LINE="$HEADER_COMMENT $GUARD_START"
    END_GUARD_LINE="$HEADER_COMMENT $GUARD_END"

        if grep -Fq "$HEADER_LINE" "$TARGET_FILE_EXPANDED"; then
        echo "Found existing managed section, updating..."

        # Use grep -n to find line numbers and awk for safer extraction
        HEADER_LINE_NUM=$(grep -Fn "$HEADER_LINE" "$TARGET_FILE_EXPANDED" | head -1 | cut -d: -f1)
        END_LINE_NUM=$(grep -Fn "$END_GUARD_LINE" "$TARGET_FILE_EXPANDED" | head -1 | cut -d: -f1)

        # Extract content before our section
        if [[ $HEADER_LINE_NUM -gt 1 ]]; then
            head -n $((HEADER_LINE_NUM - 1)) "$TARGET_FILE_EXPANDED" > "$TEMP_FILE"
        else
            > "$TEMP_FILE"  # Empty file if header is at line 1
        fi

        # Add our managed section
        echo "$HEADER_LINE" >> "$TEMP_FILE"
        echo "$START_GUARD_LINE" >> "$TEMP_FILE"
        echo "$CONTENT" >> "$TEMP_FILE"
        echo "$END_GUARD_LINE" >> "$TEMP_FILE"

        # Extract content after our section
        TOTAL_LINES=$(wc -l < "$TARGET_FILE_EXPANDED")
        if [[ $END_LINE_NUM -lt $TOTAL_LINES ]]; then
            tail -n +$((END_LINE_NUM + 1)) "$TARGET_FILE_EXPANDED" >> "$TEMP_FILE"
        fi

    else
        echo "No existing managed section found, appending..."

        # Copy existing content
        cp "$TARGET_FILE_EXPANDED" "$TEMP_FILE"

        # Add blank line if file doesn't end with one
        if [[ -s "$TEMP_FILE" ]] && [[ "$(tail -c1 "$TEMP_FILE" | wc -l)" -eq 0 ]]; then
            echo "" >> "$TEMP_FILE"
        fi

        # Add our managed section
        echo "$HEADER_LINE" >> "$TEMP_FILE"
        echo "$START_GUARD_LINE" >> "$TEMP_FILE"
        echo "$CONTENT" >> "$TEMP_FILE"
        echo "$END_GUARD_LINE" >> "$TEMP_FILE"
    fi
else
    echo "Target file doesn't exist, creating new file..."

    # Create new file with our content
    HEADER_LINE="$HEADER_COMMENT dotfiles installed $LABEL"
    START_GUARD_LINE="$HEADER_COMMENT $GUARD_START"
    END_GUARD_LINE="$HEADER_COMMENT $GUARD_END"

    echo "$HEADER_LINE" > "$TEMP_FILE"
    echo "$START_GUARD_LINE" >> "$TEMP_FILE"
    echo "$CONTENT" >> "$TEMP_FILE"
    echo "$END_GUARD_LINE" >> "$TEMP_FILE"
fi

# Atomically replace the target file
mv "$TEMP_FILE" "$TARGET_FILE_EXPANDED"
echo "Successfully installed dotfiles content to: $TARGET_FILE_EXPANDED"
