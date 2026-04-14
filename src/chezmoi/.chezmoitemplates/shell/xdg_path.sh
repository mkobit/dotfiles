# Add ~/.local/bin to PATH if it exists and isn't already in PATH
if [[ -d "{{ .chezmoi.destDir }}/.local/bin" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/bin:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/bin:$PATH"
fi

# Add ~/.local/bin/tools to PATH if it exists and isn't already in PATH
if [[ -d "{{ .chezmoi.destDir }}/.local/bin/tools" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/bin/tools:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/bin/tools:$PATH"
fi

# Add mise shims to PATH if they exist
if [[ -d "{{ .chezmoi.destDir }}/.local/share/mise/shims" && ":$PATH:" != *":{{ .chezmoi.destDir }}/.local/share/mise/shims:"* ]]; then
    export PATH="{{ .chezmoi.destDir }}/.local/share/mise/shims:$PATH"
fi
