#!/bin/bash
# Print paths to all generated dotfiles

echo "Generated dotfiles paths:"
echo "=========================="

# Loop through all inputs and print their paths
for file in "$@"; do
  echo "$file"
done

echo ""
echo "To use these files, add source-file statements to your configuration files."
echo "For tmux: echo \"source-file [PATH_TO_TMUX_CONF]\" >> ~/.tmux.conf"