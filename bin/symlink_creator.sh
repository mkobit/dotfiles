#!/bin/bash
# Helper script for creating symbolic links for dotfiles
# This script handles platform-specific symlink creation

SOURCE_FILE="$1"
TARGET_FILE="$2"

# Check if both parameters are provided
if [ -z "$SOURCE_FILE" ] || [ -z "$TARGET_FILE" ]; then
    echo "Usage: $0 <source_file> <target_file>"
    exit 1
fi

# Create parent directory if it doesn't exist
mkdir -p "$(dirname "$TARGET_FILE")"

# Handle platform-specific symlink creation
case "$(uname)" in
    "Darwin"|"Linux")
        # For macOS and Linux
        ln -sf "$SOURCE_FILE" "$TARGET_FILE"
        ;;
    "MINGW"*|"MSYS"*|"CYGWIN"*)
        # For Windows
        # Use mklink command or PowerShell to create symlinks
        powershell -Command "New-Item -ItemType SymbolicLink -Path '$TARGET_FILE' -Target '$SOURCE_FILE' -Force"
        ;;
    *)
        echo "Unsupported operating system"
        exit 1
        ;;
esac

echo "Created symlink: $TARGET_FILE -> $SOURCE_FILE"
exit 0