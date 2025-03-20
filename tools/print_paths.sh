#!/bin/bash
# Print paths to all generated dotfiles
set -euo pipefail

# Default header
header="Generated dotfiles paths:"

# Process arguments - the first arg may be a header string
if [[ $# -gt 0 ]]; then
  # Check for different colon formats
  first_arg="$1"
  first_arg="${first_arg//\"/}"  # Remove quotes if present
  if [[ "$first_arg" == *":"* ]]; then
    header="$first_arg"
    shift
  fi
fi

# All remaining args are files
files=("$@")

echo "$header"
echo "$(printf '=%.0s' $(seq 1 ${#header}))"

# Loop through all file inputs and print their paths
for file in "${files[@]}"; do
  # Check if the file exists
  if [[ -f "$file" ]]; then
    echo "$(readlink -f "$file")"
  else
    echo "$file (not found)"
  fi
done

echo ""
echo "To use these files, you can:"
echo "1. Create symlinks: ln -sf [SOURCE_PATH] [DESTINATION_PATH]"
echo "2. Add source statements (for some configs): source [PATH_TO_CONFIG]"
echo "3. For tmux: echo \"source-file [PATH_TO_TMUX_CONF]\" >> ~/.tmux.conf"
echo "4. For git: git config --global include.path [PATH_TO_GITCONFIG]"