# Add ~/.local/bin to PATH if it exists and isn't already in PATH
if [[ -d "$HOME/.local/bin" && ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Add ~/.local/bin/tools to PATH if it exists and isn't already in PATH
if [[ -d "$HOME/.local/bin/tools" && ":$PATH:" != *":$HOME/.local/bin/tools:"* ]]; then
    export PATH="$HOME/.local/bin/tools:$PATH"
fi
