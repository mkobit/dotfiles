# Add ~/.local/bin to PATH if it exists and isn't already in PATH
if [[ -d "{{ .chezmoi.destDir }}/.local/bin" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/bin:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/bin:$PATH"
fi

# Add ~/.local/bin/tools to PATH if it exists and isn't already in PATH
if [[ -d "{{ .chezmoi.destDir }}/.local/bin/tools" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/bin/tools:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/bin/tools:$PATH"
fi

# Add nvim to PATH if it exists
if [[ -d "{{ .chezmoi.destDir }}/.local/nvim/bin" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/nvim/bin:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/nvim/bin:$PATH"
fi
